"""Frozen per-step level method for the volume law test.

Onsets come from the 250 ms step grid, starting at the first rising edge after silence,
as in the grid frequency method. Each note's level is the RMS of the band-passed signal
from 50 to 90 ms after its grid onset, after the pitch glide. A step's level is the
median over its first five loops, in dB relative to step 1. Steps more than 45 dB below
step 1 are reported as silent.
"""

import math

import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "band_hz": [200.0, 8000.0],
    "onset_fraction_of_peak": 0.15,
    "envelope_window_seconds": 0.003,
    "step_seconds": 0.25,
    "steps_per_loop": 16,
    "loops": 5,
    "level_window_ms": [50.0, 90.0],
    "silent_below_db": -45.0,
    "db_tolerance": 1.5,
    "min_agreeing_loops": 4,
}


def step_levels(path, settings=SETTINGS):
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
    low, high = settings["level_window_ms"]
    steps = {}
    for n in range(settings["loops"] * settings["steps_per_loop"]):
        onset = first + n * settings["step_seconds"] * rate
        segment = mono[round(onset + low / 1000 * rate) : round(onset + high / 1000 * rate)]
        rms = float(np.sqrt(np.mean(segment**2))) if len(segment) else 0.0
        steps.setdefault(n % settings["steps_per_loop"] + 1, []).append(rms)
    return {"first_onset_seconds": first / rate}, steps


def levels_db(steps):
    base = float(np.median(steps[1]))
    if base <= 0:
        return None
    table = {}
    for step, values in sorted(steps.items()):
        median = float(np.median(values))
        table[step] = {
            "median_rms": median,
            "median_db": 20 * math.log10(median / base) if median > 0 else None,
            "loop_db": [20 * math.log10(v / base) if v > 0 else None for v in values],
        }
    return {"step1_rms": base, "steps": table}


def decide(table, models, settings=SETTINGS):
    """A model holds when every step it predicts (not None) is within the tolerance."""
    tolerance = settings["db_tolerance"]
    support = {}
    for name, predicted in models.items():
        ok = table is not None and sorted(table["steps"]) == list(range(1, 17))
        for step in range(1, 17):
            if not ok:
                break
            target = predicted[step - 1]
            if target is None:
                continue
            entry = table["steps"][step]
            close = [d is not None and abs(d - target) <= tolerance for d in entry["loop_db"]]
            ok = (
                entry["median_db"] is not None
                and abs(entry["median_db"] - target) <= tolerance
                and sum(close) >= settings["min_agreeing_loops"]
            )
        support[name] = ok
    supported = [name for name, ok in support.items() if ok]
    return {
        "model_support": support,
        "classification": supported[0] if len(supported) == 1 else "other_or_inconclusive",
    }
