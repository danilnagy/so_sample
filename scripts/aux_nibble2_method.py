"""Frozen measurement method for the aux-nibble-002 test (docs/aux-nibble-2-control.md).

Reads the recorded playback of experiments/aux-nibble-002 (60 BPM, no swing, a chain of 14
one-bar patterns, 56 s a pass) and measures:

- the drum (Sound 9): onsets of its 7 kHz click, counted within the step of each retrigger
  of 4 (with 0, 1, 2 and 3 other voices held), and the power of its 2 to 4 kHz noise body in
  a window 12 to 52 ms after an onset;
- the single-hit reference (Pattern 1, step 1): its body power in the same window after
  offsets of 0, 62.5, 125 and 187.5 ms, from which the power after the fourth of four
  overlapping repeats is predicted;
- the choke ratio: the body power after the fourth onset of the unaccompanied retrigger
  (Pattern 1, step 9) over the reference's power after its own onset, in dB;
- the holders (Sounds 1 to 3 at 250, 350 and 500 Hz) and the length probes (Sounds 5 and 6
  at 700 and 1000 Hz): how long each sounds, from its onset to the first fall below a tenth
  of its peak;
- exploratory: the click onsets in the two FX drum patterns and the 700 Hz tone's sounding
  intervals in the two FX melodic patterns.

The first sound of the chain is the reference click, so the first click onset starts the
first pass; each probe is looked for near its time on the 60 BPM grid and anchored on its own
onset. Every full pass is measured; the decision takes the majority (counts) or the median
(durations, powers) over passes.

This module is pinned by hash in the registration.
"""

import numpy as np
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "step_seconds": 0.25,
    "steps_per_pattern": 16,
    "chain_patterns": 14,
    "click_band_hz": [6000.0, 8500.0],
    "body_band_hz": [2000.0, 4000.0],
    "tone_bands_hz": {"250": [215.0, 290.0], "350": [300.0, 410.0], "500": [430.0, 580.0], "700": [600.0, 820.0], "1000": [860.0, 1180.0]},
    "click_hop_seconds": 0.001,
    "tone_hop_seconds": 0.01,
    "onset_on_fraction": 0.3,
    "onset_off_fraction": 0.1,
    "onset_min_gap_seconds": 0.01,
    "search_seconds": 0.12,
    "own_step_tolerance_seconds": 0.03,
    "body_window_seconds": [0.012, 0.052],
    "reference_offsets_seconds": [0.0, 0.0625, 0.125, 0.1875],
    "tone_floor_fraction": 0.1,
    "tone_window_steps": 24,
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


def power(x, rate, start, window):
    a, b = int((start + window[0]) * rate), int((start + window[1]) * rate)
    seg = x[max(0, a) : max(0, b)]
    return float(np.mean(seg**2)) if len(seg) else 0.0


def tone_duration(env, hop, expected, s, step):
    lo = max(0, int((expected - s["search_seconds"]) / hop))
    hi = min(len(env), int((expected + s["tone_window_steps"] * step - s["search_seconds"]) / hop))
    segment = env[lo:hi]
    if len(segment) == 0 or segment.max() <= 0:
        return None
    floor = s["tone_floor_fraction"] * float(segment.max())
    above = np.flatnonzero(segment >= floor)
    first = int(above[0])
    below = np.flatnonzero(segment[first:] < floor)
    end = first + (int(below[0]) if len(below) else len(segment) - first)
    return {"onset_seconds": (lo + first) * hop, "duration_seconds": round((end - first) * hop, 3)}


def tone_intervals(env, hop, start, seconds, floor):
    """Sounding intervals [on, off] (seconds after `start`) of a tone envelope above `floor`."""
    lo, hi = int(start / hop), min(len(env), int((start + seconds) / hop))
    on = env[lo:hi] >= floor
    out, begin = [], None
    for i, v in enumerate(on):
        if v and begin is None:
            begin = i
        elif not v and begin is not None:
            out.append([round(begin * hop, 3), round(i * hop, 3)])
            begin = None
    if begin is not None:
        out.append([round(begin * hop, 3), round(len(on) * hop, 3)])
    return out


def measure(samples, rate, probes, settings=SETTINGS):
    """Per-pass measurements; `probes` is the registration's probe layout."""
    s = settings
    step = s["step_seconds"]
    x = mono(np.asarray(samples, dtype=float))
    click_env, click_hop = envelope(band(x, rate, *s["click_band_hz"]), rate, s["click_hop_seconds"])
    body = band(x, rate, *s["body_band_hz"])
    tone_envs = {k: envelope(band(x, rate, *b), rate, s["tone_hop_seconds"]) for k, b in s["tone_bands_hz"].items()}
    click_peak = float(click_env.max())
    if click_peak < s["min_click_level"]:
        raise ValueError("No click in the playback recording (silent or wrong input)")
    clicks = onset_times(
        click_env, click_hop, s["onset_on_fraction"] * click_peak, s["onset_off_fraction"] * click_peak, s["onset_min_gap_seconds"]
    )
    if not clicks:
        raise ValueError("No click onsets in the playback recording")
    grid = lambda t0, p: t0 + ((p["pattern"] - 1) * s["steps_per_pattern"] + p["step"] - 1) * step
    cycle = s["chain_patterns"] * s["steps_per_pattern"] * step
    duration = len(x) / rate
    start = clicks[0]
    passes = []
    k = 0
    while start + (k + 1) * cycle <= duration + step:
        t0 = start + k * cycle

        def click_probe(p, t0=t0, window_steps=1.0):
            expected = grid(t0, p)
            near = [t for t in clicks if abs(t - expected) <= s["search_seconds"]]
            if not near:
                return {"found": False}
            anchor = near[0]
            limit = anchor + window_steps * step + s["own_step_tolerance_seconds"]
            onsets = [t for t in clicks if anchor <= t < limit]
            return {"found": True, "anchor_seconds": anchor, "drift_seconds": anchor - expected, "onsets": onsets}

        ref = click_probe(probes["reference"])
        ref_powers = [power(body, rate, ref["anchor_seconds"] + o, s["body_window_seconds"]) for o in s["reference_offsets_seconds"]] if ref["found"] else None
        voices = []
        for v in probes["voice_probes"]:
            r = click_probe(v["probe"])
            row = {"held": v["held"], "found": r["found"]}
            if r["found"]:
                row["own_step_onsets"] = len(r["onsets"])
                row["onset_offsets_seconds"] = [round(t - r["anchor_seconds"], 4) for t in r["onsets"]]
                row["power_after_last_onset"] = power(body, rate, r["onsets"][-1], s["body_window_seconds"])
            voices.append(row)
        holders = []
        for p in probes["holder_probes"]:
            env, hop = tone_envs[str(probes["hz_by_sound"][str(p["sound"])])]
            holders.append({**p, **(tone_duration(env, hop, grid(t0, p), s, step) or {"found": False})})
        lengths = []
        for p in probes["length_probes"]:
            env, hop = tone_envs[str(probes["hz_by_sound"][str(p["sound"])])]
            lengths.append({**p, "nibble_hex": format(p["nibble"], "X"), **(tone_duration(env, hop, grid(t0, p), s, step) or {"found": False})})
        fx = []
        for f in probes["fx_patterns"]:
            pattern_start = t0 + (f["pattern"] - 1) * s["steps_per_pattern"] * step
            row = {"pattern": f["pattern"], "fx": f["fx"], "held_steps": f["held"], "probe": f["probe"]}
            if f["probe"]["sound"] == probes["drum_sound"]:
                row["click_onsets_seconds_in_pattern"] = [
                    round(t - pattern_start, 4) for t in clicks if pattern_start - 0.02 <= t < pattern_start + s["steps_per_pattern"] * step - 0.02
                ]
            else:
                env, hop = tone_envs[str(probes["hz_by_sound"][str(f["probe"]["sound"])])]
                floor = s["tone_floor_fraction"] * float(env.max())
                row["tone_intervals_seconds_in_pattern"] = tone_intervals(env, hop, pattern_start, s["steps_per_pattern"] * step, floor)
            fx.append(row)
        passes.append(
            {
                "pass": k + 1,
                "start_seconds": t0,
                "reference_found": ref["found"],
                "reference_body_powers": ref_powers,
                "voices": voices,
                "holders": holders,
                "lengths": lengths,
                "fx": fx,
            }
        )
        k += 1
    return {"first_onset_seconds": start, "click_peak": click_peak, "passes": passes}


def _majority(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    counts = {v: values.count(v) for v in set(values)}
    best = max(counts.values())
    winners = [v for v, c in counts.items() if c == best]
    return winners[0] if len(winners) == 1 else None


def _median(values):
    values = [v for v in values if v is not None]
    return float(np.median(values)) if values else None


def summarize(measurements):
    """The per-quantity values the predictions are judged on, over all passes."""
    passes = measurements["passes"]
    if not passes:
        raise ValueError("No full pass of the chain in the recording")
    onsets_by_held = {}
    for held in range(4):
        rows = [v for p in passes for v in p["voices"] if v["held"] == held and v["found"]]
        onsets_by_held[str(held)] = _majority([r["own_step_onsets"] for r in rows])
    # Choke: power after the fourth onset of the unaccompanied retrigger, over the reference's own.
    ratios, predicted = [], []
    for p in passes:
        control = next(v for v in p["voices"] if v["held"] == 0)
        ref = p["reference_body_powers"]
        if not (control["found"] and ref and ref[0] > 0 and control["own_step_onsets"] == 4):
            continue
        ratios.append(10 * np.log10(control["power_after_last_onset"] / ref[0]))
        predicted.append(10 * np.log10(sum(ref) / ref[0]))
    holder_seconds = {}
    for row in passes[0]["holders"]:
        key = f"{row['pattern']}:{row['sound']}"
        holder_seconds[key] = _median(
            [h.get("duration_seconds") for p in passes for h in p["holders"] if f"{h['pattern']}:{h['sound']}" == key]
        )
    length_seconds = {}
    for row in passes[0]["lengths"]:
        n = row["nibble_hex"]
        length_seconds[n] = _median([r.get("duration_seconds") for p in passes for r in p["lengths"] if r["nibble_hex"] == n])
    return {
        "own_step_onsets_by_voices_held": onsets_by_held,
        "choke_ratio_db": round(_median(ratios), 2) if ratios else None,
        "overlap_predicted_db": round(_median(predicted), 2) if predicted else None,
        "holder_seconds": holder_seconds,
        "length_seconds_by_nibble": length_seconds,
    }


def decide(measurements, predictions):
    """Each registered prediction held or failed."""
    summary = summarize(measurements)
    results = {}
    for name, rule in predictions.items():
        kind = rule["kind"]
        if kind == "voice_onsets":
            got = summary["own_step_onsets_by_voices_held"]
            mismatches = [[h, e, got.get(h)] for h, e in rule["expected"].items() if got.get(h) != e]
        elif kind == "choke":
            ratio, pred = summary["choke_ratio_db"], summary["overlap_predicted_db"]
            target = 0.0 if rule["model"] == "restart" else pred
            ok = ratio is not None and target is not None and (rule["model"] == "restart" or pred >= rule["min_separation_db"])
            mismatches = [] if ok and abs(ratio - target) <= rule["tolerance_db"] else [[rule["model"], target, ratio]]
        elif kind == "holder_duration":
            got = summary["holder_seconds"]
            mismatches = [[k, rule["expected_seconds"], v] for k, v in got.items() if v is None or abs(v - rule["expected_seconds"]) > rule["tolerance_seconds"]]
        else:  # melodic_duration
            got = summary["length_seconds_by_nibble"]
            mismatches = [
                [n, e, got.get(n)] for n, e in rule["expected_seconds"].items() if got.get(n) is None or abs(got[n] - e) > rule["tolerance_seconds"]
            ]
        results[name] = {"holds": not mismatches, "mismatches": mismatches}
    return {**summary, "predictions": results}
