"""Frozen measurement method for the aux-nibble-003 test (docs/aux-nibble-3-control.md).

Reads the recorded playback of experiments/aux-nibble-003 (120 BPM, swing 12, a chain of
seven one-bar patterns, 14 s a pass) and measures:

- each drum probe (a 6 ms 5 kHz click, retriggers 2, 3, 4, 6, 8 on odd and even steps): its
  onsets from its first onset over 2.3 steps, their count, and the median spacing of the
  first n onsets (n the retrigger), and its first onset's offset from the unswung grid;
- each melodic probe (lengths 1 to 4; a 700 Hz tone on Sound 1 at step 1, a 1000 Hz tone on
  Sound 2 at step 2): how long it sounds, from its onset to the first fall below a tenth of
  its peak, in its own tone's band.

The first sound of the chain is the drum probe on Pattern 1, step 1, so the first click
onset starts the first pass. Even steps are looked for where swing puts them (swing / 24 of
a step late, swing-law-results.md) and every probe is anchored on its own onset. Every full
pass is measured; the decision takes the median over passes.

This module is pinned by hash in the registration.
"""

import numpy as np
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "step_seconds": 0.125,
    "swing_delay_seconds": 0.0625,
    "steps_per_pattern": 16,
    "chain_patterns": 7,
    "click_band_hz": [3800.0, 6500.0],
    "tone_bands_hz": {"1": [600.0, 820.0], "2": [860.0, 1180.0]},
    "click_hop_seconds": 0.0005,
    "tone_hop_seconds": 0.005,
    "onset_on_fraction": 0.3,
    "onset_off_fraction": 0.1,
    "onset_min_gap_seconds": 0.006,
    "search_seconds": 0.04,
    "drum_window_steps": 2.3,
    "tone_floor_fraction": 0.1,
    "tone_window_steps": 10,
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


def measure(samples, rate, drum_probes, melodic_probes, settings=SETTINGS):
    s = settings
    step = s["step_seconds"]
    x = mono(np.asarray(samples, dtype=float))
    click_env, click_hop = envelope(band(x, rate, *s["click_band_hz"]), rate, s["click_hop_seconds"])
    tone_envs = {k: envelope(band(x, rate, *b), rate, s["tone_hop_seconds"]) for k, b in s["tone_bands_hz"].items()}
    click_peak = float(click_env.max())
    if click_peak < s["min_click_level"]:
        raise ValueError("No click in the playback recording (silent or wrong input)")
    clicks = onset_times(
        click_env, click_hop, s["onset_on_fraction"] * click_peak, s["onset_off_fraction"] * click_peak, s["onset_min_gap_seconds"]
    )
    if not clicks:
        raise ValueError("No click onsets in the playback recording")
    cycle = s["chain_patterns"] * s["steps_per_pattern"] * step
    duration = len(x) / rate
    start = clicks[0]
    passes = []
    k = 0
    while start + (k + 1) * cycle <= duration + step:
        t0 = start + k * cycle
        row = {"pass": k + 1, "start_seconds": t0, "drum": [], "melodic": []}
        for p in drum_probes:
            grid = t0 + ((p["pattern"] - 1) * s["steps_per_pattern"] + p["step"] - 1) * step
            expected = grid + (s["swing_delay_seconds"] if p["step"] % 2 == 0 else 0.0)
            near = [t for t in clicks if abs(t - expected) <= s["search_seconds"]]
            if not near:
                row["drum"].append({**p, "found": False})
                continue
            anchor = near[0]
            onsets = [t for t in clicks if anchor <= t < anchor + s["drum_window_steps"] * step]
            first = onsets[: p["nibble"]]
            gaps = np.diff(first)
            row["drum"].append(
                {
                    **p,
                    "found": True,
                    "parity": "even" if p["step"] % 2 == 0 else "odd",
                    "offset_from_grid_seconds": round(anchor - grid, 4),
                    "onsets": len(onsets),
                    "onset_offsets_seconds": [round(t - anchor, 4) for t in onsets],
                    "spacing_seconds": round(float(np.median(gaps)), 4) if len(gaps) else None,
                }
            )
        for p in melodic_probes:
            tone_env, tone_hop = tone_envs[str(p["sound"])]
            grid = t0 + ((p["pattern"] - 1) * s["steps_per_pattern"] + p["step"] - 1) * step
            expected = grid + (s["swing_delay_seconds"] if p["step"] % 2 == 0 else 0.0)
            lo = max(0, int((expected - s["search_seconds"]) / tone_hop))
            hi = min(len(tone_env), int((expected + s["tone_window_steps"] * step) / tone_hop))
            segment = tone_env[lo:hi]
            if len(segment) == 0 or segment.max() <= 0:
                row["melodic"].append({**p, "found": False})
                continue
            floor = s["tone_floor_fraction"] * float(segment.max())
            first = int(np.flatnonzero(segment >= floor)[0])
            below = np.flatnonzero(segment[first:] < floor)
            end = first + (int(below[0]) if len(below) else len(segment) - first)
            row["melodic"].append(
                {
                    **p,
                    "found": True,
                    "parity": "even" if p["step"] % 2 == 0 else "odd",
                    "offset_from_grid_seconds": round((lo + first) * tone_hop - grid, 4),
                    "duration_seconds": round((end - first) * tone_hop, 4),
                }
            )
        passes.append(row)
        k += 1
    return {"first_onset_seconds": start, "click_peak": click_peak, "passes": passes}


def _median(values):
    values = [v for v in values if v is not None]
    return float(np.median(values)) if values else None


def summarize(measurements):
    passes = measurements["passes"]
    if not passes:
        raise ValueError("No full pass of the chain in the recording")
    spacing, counts, drum_offsets = {}, {}, {}
    for probe in passes[0]["drum"]:
        key = f"{probe['nibble']}{'e' if probe['step'] % 2 == 0 else 'o'}"
        rows = [r for p in passes for r in p["drum"] if r["nibble"] == probe["nibble"] and r["step"] == probe["step"] and r.get("found")]
        spacing[key] = _median([r["spacing_seconds"] for r in rows])
        counts[key] = _median([r["onsets"] for r in rows])
        drum_offsets[key] = _median([r["offset_from_grid_seconds"] for r in rows])
    durations, mel_offsets = {}, {}
    for probe in passes[0]["melodic"]:
        key = f"{probe['nibble']}{'e' if probe['step'] % 2 == 0 else 'o'}"
        rows = [r for p in passes for r in p["melodic"] if r["nibble"] == probe["nibble"] and r["step"] == probe["step"] and r.get("found")]
        durations[key] = _median([r["duration_seconds"] for r in rows])
        mel_offsets[key] = _median([r["offset_from_grid_seconds"] for r in rows])
    return {
        "drum_spacing_seconds": spacing,
        "drum_onsets_in_window": counts,
        "drum_offset_from_grid_seconds": drum_offsets,
        "melodic_duration_seconds": durations,
        "melodic_offset_from_grid_seconds": mel_offsets,
    }


def decide(measurements, predictions):
    """Each registered prediction held or failed: every listed value within its tolerance."""
    summary = summarize(measurements)
    results = {}
    for name, rule in predictions.items():
        got = summary["drum_spacing_seconds"] if rule["kind"] == "drum_spacing" else summary["melodic_duration_seconds"]
        mismatches = [
            [k, e, got.get(k)] for k, e in rule["expected_seconds"].items() if got.get(k) is None or abs(got[k] - e) > rule["tolerance_seconds"]
        ]
        results[name] = {"holds": not mismatches, "mismatches": mismatches}
    return {**summary, "predictions": results}
