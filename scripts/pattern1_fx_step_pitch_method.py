"""Frozen time-resolved pitch method for the step-1 effect test.

Registered before fresh recordings (see prepare_pattern1_fx_order_pitch_track.py). The
pitch track is the exploratory one, copied here so later edits elsewhere cannot change
it: band-pass, then the dominant pitch in 20 ms Hann windows every 10 ms from each
loop's onset, over the first five loops.

Step 1 is classified from 20 to 130 ms after onset, using windows whose amplitude is at
least 20% of the recording peak:
- "effect" when the highest pitch reaches 10% above the reference
- "none" when every pitch stays within 1% of the reference
- otherwise "indeterminate"
"""

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "band_hz": [600.0, 3500.0],
    "search_hz": [900.0, 2700.0],
    "window_seconds": 0.02,
    "hop_seconds": 0.01,
    "track_seconds": 0.4,
    "onset_fraction_of_peak": 0.15,
    "min_loop_gap_seconds": 1.0,
    "loops": 5,
    "fft_size": 32768,
    "step1_window_ms": [20.0, 130.0],
    "min_relative_amplitude": 0.2,
    "effect_min_rise": 0.10,
    "none_max_deviation": 0.01,
    "min_agreeing_loops": 4,
}


def pitch_track(path, settings=SETTINGS):
    samples, rate = sf.read(str(path), always_2d=True)
    mono = samples.mean(axis=1)
    sos = butter(4, settings["band_hz"], btype="band", fs=rate, output="sos")
    mono = sosfiltfilt(sos, mono)
    envelope = np.abs(mono)
    peak = envelope.max()
    above = np.flatnonzero(envelope > settings["onset_fraction_of_peak"] * peak)
    if not len(above):
        raise ValueError("No sound found in the playback recording")
    onsets = [int(above[0])]
    for index in above:
        if index - onsets[-1] > settings["min_loop_gap_seconds"] * rate:
            onsets.append(int(index))
    window = round(settings["window_seconds"] * rate)
    hop = round(settings["hop_seconds"] * rate)
    size = settings["fft_size"]
    freqs = np.fft.rfftfreq(size, 1 / rate)
    band = (freqs > settings["search_hz"][0]) & (freqs < settings["search_hz"][1])
    indices = np.flatnonzero(band)
    loops = []
    for onset in onsets[: settings["loops"]]:
        hz, amp = [], []
        for start in range(0, round(settings["track_seconds"] * rate), hop):
            segment = mono[onset + start : onset + start + window]
            if len(segment) < window:
                break
            spectrum = np.abs(np.fft.rfft(segment * np.hanning(window), size))
            k = indices[np.argmax(spectrum[band])]
            a, b, c = np.log(spectrum[k - 1 : k + 2] + 1e-12)
            curvature = a - 2 * b + c
            delta = 0.5 * (a - c) / curvature if curvature != 0 else 0.0
            hz.append(float((k + delta) * rate / size))
            amp.append(float(np.abs(segment).max() / peak))
        loops.append({"onset_seconds": onset / rate, "hz": hz, "relative_amplitude": amp})
    length = min(len(loop["hz"]) for loop in loops)
    times = [round(i * settings["hop_seconds"] * 1000, 1) for i in range(length)]
    median = {
        "hz": np.median([loop["hz"][:length] for loop in loops], axis=0).tolist(),
        "relative_amplitude": np.median(
            [loop["relative_amplitude"][:length] for loop in loops], axis=0
        ).tolist(),
    }
    return {"times_ms": times, "loops": loops, "median": median, "loop_count": len(loops)}


def classify_step1(times, hz, amplitude, reference_hz, settings=SETTINGS):
    low, high = settings["step1_window_ms"]
    values = [
        f
        for t, f, a in zip(times, hz, amplitude)
        if low <= t <= high and a >= settings["min_relative_amplitude"]
    ]
    if len(values) < 5:
        return {"class": "indeterminate", "reason": "too few audible windows", "values": values}
    ratios = [f / reference_hz for f in values]
    if max(ratios) >= 1 + settings["effect_min_rise"]:
        label = "effect"
    elif all(abs(r - 1) <= settings["none_max_deviation"] for r in ratios):
        label = "none"
    else:
        label = "indeterminate"
    return {
        "class": label,
        "max_ratio": max(ratios),
        "min_ratio": min(ratios),
        "windows": len(values),
    }


def leg_step1(track, reference_hz, settings=SETTINGS):
    times = track["times_ms"]
    median = classify_step1(
        times, track["median"]["hz"], track["median"]["relative_amplitude"], reference_hz, settings
    )
    loops = [
        classify_step1(times, loop["hz"], loop["relative_amplitude"], reference_hz, settings)
        for loop in track["loops"]
    ]
    return {"median": median, "loops": loops}


def decide(a_step1, b_step1, settings=SETTINGS):
    """Registered decision from both legs' step-1 classifications."""
    predictions = {
        "high_nibble_first": {"a": "none", "b": "effect"},
        "low_nibble_first": {"a": "effect", "b": "none"},
    }
    support = {}
    for model, expected in predictions.items():
        ok = True
        for leg, result in (("a", a_step1), ("b", b_step1)):
            agreeing = sum(loop["class"] == expected[leg] for loop in result["loops"])
            ok = ok and result["median"]["class"] == expected[leg]
            ok = ok and agreeing >= settings["min_agreeing_loops"]
        support[model] = ok
    supported = [model for model, ok in support.items() if ok]
    return {
        "model_support": support,
        "classification": supported[0] if len(supported) == 1 else "inconclusive",
    }
