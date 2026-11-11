"""Frozen measurement method for the aux-nibble test (docs/aux-nibble-control.md).

Reads the recorded playback of experiments/aux-nibble-001 and measures, for each probe:

- drum probes: the onsets of the 3 kHz click from the probe's step until the next probe
  (eight steps), counted within the probe's own step and over the whole eight steps;
- melodic probes: how long the 500 Hz tone sounds, from its onset to where it falls below a
  tenth of its peak level.

The recording starts before PLAY is pressed; the chain's first sound is the drum probe on
Pattern 1, step 1, so the first click onset is the start of the first pass. Each probe is
then looked for near its expected time on the 60 BPM grid and re-anchored on its own onset,
so a small clock difference does not accumulate. Every full pass of the chain in the
recording is measured; the decision takes the majority over passes.

This module is pinned by hash in the registration: changing it after the session voids the
frozen method.
"""

import numpy as np
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "step_seconds": 0.25,
    "steps_per_pattern": 16,
    "chain_patterns": 10,
    "click_band_hz": [2000.0, 4500.0],
    "tone_band_hz": [380.0, 650.0],
    "click_hop_seconds": 0.002,
    "tone_hop_seconds": 0.01,
    "onset_on_fraction": 0.3,
    "onset_off_fraction": 0.1,
    "onset_min_gap_seconds": 0.012,
    "search_seconds": 0.12,
    "own_step_tolerance_seconds": 0.03,
    "drum_window_steps": 8,
    "tone_floor_fraction": 0.1,
    "tone_window_steps": 16,
    "min_click_level": 0.001,
}


def mono(samples):
    return samples.mean(axis=1) if samples.ndim == 2 else samples


def band(x, rate, low, high):
    sos = butter(4, [low, high], btype="bandpass", fs=rate, output="sos")
    return sosfiltfilt(sos, x)


def envelope(x, rate, hop_seconds):
    hop = max(1, round(hop_seconds * rate))
    count = len(x) // hop
    return np.abs(x[: count * hop]).reshape(count, hop).max(axis=1), hop / rate


def onset_times(env, hop_s, on_level, off_level, min_gap_s):
    """Rising crossings of on_level, each after the envelope fell below off_level."""
    times, armed, last = [], True, -1.0
    for i, v in enumerate(env):
        t = i * hop_s
        if armed and v >= on_level and t - last >= min_gap_s:
            times.append(t)
            armed, last = False, t
        elif not armed and v < off_level:
            armed = True
    return times


def measure(samples, rate, drum_probes, melodic_probes, tone_seconds, settings=SETTINGS):
    """Per-pass measurements of every probe; see the module docstring."""
    s = settings
    x = mono(np.asarray(samples, dtype=float))
    click_env, click_hop = envelope(band(x, rate, *s["click_band_hz"]), rate, s["click_hop_seconds"])
    tone_env, tone_hop = envelope(band(x, rate, *s["tone_band_hz"]), rate, s["tone_hop_seconds"])
    click_peak = float(click_env.max())
    if click_peak < s["min_click_level"]:
        raise ValueError("No click in the playback recording (silent or wrong input)")
    clicks = onset_times(
        click_env,
        click_hop,
        s["onset_on_fraction"] * click_peak,
        s["onset_off_fraction"] * click_peak,
        s["onset_min_gap_seconds"],
    )
    if not clicks:
        raise ValueError("No click onsets in the playback recording")
    step = s["step_seconds"]
    cycle = s["chain_patterns"] * s["steps_per_pattern"] * step
    duration = len(x) / rate
    start = clicks[0]
    passes = []
    p = 0
    while start + (p + 1) * cycle <= duration + step:
        t0 = start + p * cycle
        row = {"pass": p + 1, "start_seconds": t0, "drum": [], "melodic": []}
        for probe in drum_probes:
            expected = t0 + ((probe["pattern"] - 1) * s["steps_per_pattern"] + probe["step"] - 1) * step
            near = [t for t in clicks if abs(t - expected) <= s["search_seconds"]]
            if not near:
                row["drum"].append({**probe, "found": False})
                continue
            anchor = near[0]
            window = [t - anchor for t in clicks if anchor <= t < anchor + s["drum_window_steps"] * step - s["search_seconds"]]
            own = [d for d in window if d < step + s["own_step_tolerance_seconds"]]
            row["drum"].append(
                {
                    **probe,
                    "found": True,
                    "anchor_seconds": anchor,
                    "drift_seconds": anchor - expected,
                    "own_step_onsets": len(own),
                    "window_onsets": len(window),
                    "onset_offsets_seconds": [round(d, 4) for d in window],
                }
            )
        for probe in melodic_probes:
            expected = t0 + ((probe["pattern"] - 1) * s["steps_per_pattern"] + probe["step"] - 1) * step
            lo = max(0, int((expected - s["search_seconds"]) / tone_hop))
            hi = min(len(tone_env), int((expected + s["tone_window_steps"] * step - s["search_seconds"]) / tone_hop))
            segment = tone_env[lo:hi]
            if len(segment) == 0 or segment.max() <= 0:
                row["melodic"].append({**probe, "found": False})
                continue
            floor = s["tone_floor_fraction"] * float(segment.max())
            above = np.flatnonzero(segment >= floor)
            first = int(above[0])
            # The note's end: the first fall below the floor after its onset (not a later sound).
            below = np.flatnonzero(segment[first:] < floor)
            end = first + (int(below[0]) if len(below) else len(segment) - first)
            row["melodic"].append(
                {
                    **probe,
                    "found": True,
                    "onset_seconds": (lo + first) * tone_hop,
                    "drift_seconds": (lo + first) * tone_hop - expected,
                    "duration_seconds": round((end - first) * tone_hop, 3),
                    "duration_steps": round((end - first) * tone_hop / step, 2),
                    "full_tone_seconds": tone_seconds,
                }
            )
        passes.append(row)
        p += 1
    return {"first_onset_seconds": start, "click_peak": click_peak, "passes": passes}


def _majority(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    counts = {v: values.count(v) for v in set(values)}
    best = max(counts.values())
    winners = [v for v, c in counts.items() if c == best]
    return winners[0] if len(winners) == 1 else None


def decide(measurements, predictions):
    """Each registered prediction held or failed, by majority over the passes."""
    passes = measurements["passes"]
    if not passes:
        raise ValueError("No full pass of the chain in the recording")
    drum = {}
    for probe in passes[0]["drum"]:
        n = probe["nibble"]
        rows = [r for p in passes for r in p["drum"] if r["nibble"] == n and r.get("found")]
        drum[n] = _majority([r["own_step_onsets"] for r in rows])
    melodic = {}
    for probe in passes[0]["melodic"]:
        n = probe["nibble"]
        rows = [r for p in passes for r in p["melodic"] if r["nibble"] == n and r.get("found")]
        melodic[n] = float(np.median([r["duration_seconds"] for r in rows])) if rows else None
    results = {}
    for name, rule in predictions.items():
        if rule["kind"] == "drum_onsets":
            mismatches = [
                [int(n), expected, drum.get(int(n))]
                for n, expected in rule["expected"].items()
                if drum.get(int(n)) != expected
            ]
        else:
            mismatches = [
                [int(n, 16), expected, melodic.get(int(n, 16))]
                for n, expected in rule["expected_seconds"].items()
                if melodic.get(int(n, 16)) is None or abs(melodic[int(n, 16)] - expected) > rule["tolerance_seconds"]
            ]
        results[name] = {"holds": not mismatches, "mismatches": mismatches}
    return {
        "drum_own_step_onsets_by_nibble": {str(k): v for k, v in drum.items()},
        "melodic_duration_seconds_by_nibble": {format(k, "X"): v for k, v in melodic.items()},
        "predictions": results,
    }
