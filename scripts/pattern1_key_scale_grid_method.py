"""Frozen grid-only frequency method for the keyboard scale map rerun.

Lessons from the first run: low keys play the sample slower and last longer than a
step, and a new note cuts the previous one, so there is no silence between notes. The
first note's onset is the first rising edge after silence; every later onset is taken
purely from the step grid (250 ms at 60 BPM). Pitch is the median dominant frequency of
20 ms Hann windows starting 5, 10, 15 and 20 ms after each grid onset, searched from
300 Hz to 7.5 kHz. Intervals are in cents relative to step 1.
"""

import math

import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "band_hz": [200.0, 8000.0],
    "search_hz": [300.0, 7500.0],
    "onset_fraction_of_peak": 0.15,
    "envelope_window_seconds": 0.003,
    "step_seconds": 0.25,
    "steps_per_loop": 16,
    "loops": 5,
    "window_seconds": 0.02,
    "window_starts_ms": [5.0, 10.0, 15.0, 20.0],
    "min_window_level_of_peak": 0.05,
    "fft_size": 32768,
    "cents_tolerance": 20.0,
    "min_agreeing_loops": 4,
}


def _pitch(segment, rate, settings):
    size = settings["fft_size"]
    freqs = np.fft.rfftfreq(size, 1 / rate)
    band = (freqs > settings["search_hz"][0]) & (freqs < settings["search_hz"][1])
    indices = np.flatnonzero(band)
    spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment)), size))
    k = indices[np.argmax(spectrum[band])]
    a, b, c = np.log(spectrum[k - 1 : k + 2] + 1e-12)
    curvature = a - 2 * b + c
    delta = 0.5 * (a - c) / curvature if curvature != 0 else 0.0
    return float((k + delta) * rate / size)


def step_frequencies(path, settings=SETTINGS):
    samples, rate = sf.read(str(path), always_2d=True)
    sos = butter(4, settings["band_hz"], btype="band", fs=rate, output="sos")
    mono = sosfiltfilt(sos, samples.mean(axis=1))
    envelope = maximum_filter1d(
        np.abs(mono), max(1, round(settings["envelope_window_seconds"] * rate))
    )
    peak = envelope.max()
    above = envelope > settings["onset_fraction_of_peak"] * peak
    rising = np.flatnonzero(above[1:] & ~above[:-1]) + 1
    if above[0] or not len(rising):
        raise ValueError("The recording must start in silence before the first note")
    first = int(rising[0])
    window = round(settings["window_seconds"] * rate)
    steps, missing = {}, []
    for n in range(settings["loops"] * settings["steps_per_loop"]):
        onset = first + n * settings["step_seconds"] * rate
        values = []
        for start_ms in settings["window_starts_ms"]:
            begin = round(onset + start_ms / 1000 * rate)
            segment = mono[begin : begin + window]
            if len(segment) < window:
                continue
            if np.abs(segment).max() < settings["min_window_level_of_peak"] * peak:
                continue
            values.append(_pitch(segment, rate, settings))
        step = n % settings["steps_per_loop"] + 1
        if values:
            steps.setdefault(step, []).append(float(np.median(values)))
        else:
            steps.setdefault(step, []).append(None)
            missing.append(n)
    return {"first_onset_seconds": first / rate, "missing": missing}, steps


def intervals(steps):
    reference = [f for f in steps.get(1, []) if f is not None]
    if not reference:
        return None
    base = float(np.median(reference))
    table = {}
    for step, values in sorted(steps.items()):
        usable = [f for f in values if f is not None]
        table[step] = {
            "median_hz": float(np.median(usable)) if usable else None,
            "median_cents": 1200 * math.log2(np.median(usable) / base) if usable else None,
            "loop_cents": [None if f is None else 1200 * math.log2(f / base) for f in values],
        }
    return {"step1_hz": base, "steps": table}


def decide(table, models, settings=SETTINGS):
    tolerance = settings["cents_tolerance"]
    support = {}
    for name, cents in models.items():
        ok = table is not None and sorted(table["steps"]) == list(range(1, 17))
        for step in range(1, 17):
            if not ok:
                break
            entry = table["steps"][step]
            target = cents[step - 1]
            close = [c is not None and abs(c - target) <= tolerance for c in entry["loop_cents"]]
            ok = (
                entry["median_cents"] is not None
                and abs(entry["median_cents"] - target) <= tolerance
                and sum(close) >= settings["min_agreeing_loops"]
            )
        support[name] = ok
    supported = [name for name, ok in support.items() if ok]
    return {
        "model_support": support,
        "classification": supported[0] if len(supported) == 1 else "other_or_inconclusive",
    }
