"""Frozen method: how long each pattern step sounds, for tones that end before the next step.

The first note's onset is the first rising edge after silence; later steps follow the
step grid. Each step is searched from 10 ms before its grid onset to 10 ms before the next
one. In that span the band-passed envelope (1 ms maximum filter) is compared with 10% of
the span's peak: the sounding duration runs from the first sample above it to the last.
"""

import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "band_hz": [200.0, 8000.0],
    "onset_fraction_of_peak": 0.15,
    "envelope_window_seconds": 0.001,
    "step_seconds": 0.25,
    "steps_per_loop": 16,
    "loops": 5,
    "margin_seconds": 0.01,
    "threshold_fraction_of_step_peak": 0.1,
    "tolerance_ms": 5.0,
    "min_agreeing_loops": 4,
}


def step_durations(path, settings=SETTINGS):
    samples, rate = sf.read(str(path), always_2d=True)
    sos = butter(4, settings["band_hz"], btype="band", fs=rate, output="sos")
    mono = sosfiltfilt(sos, samples.mean(axis=1))
    envelope = maximum_filter1d(
        np.abs(mono), max(1, round(settings["envelope_window_seconds"] * rate))
    )
    above = envelope > settings["onset_fraction_of_peak"] * envelope.max()
    rising = np.flatnonzero(above[1:] & ~above[:-1]) + 1
    if above[0] or not len(rising):
        raise ValueError("The recording must start in silence before the first note")
    first = int(rising[0])
    margin = settings["margin_seconds"] * rate
    durations = {}
    for n in range(settings["loops"] * settings["steps_per_loop"]):
        grid = first + n * settings["step_seconds"] * rate
        begin, end = round(grid - margin), round(grid + settings["step_seconds"] * rate - margin)
        span = envelope[max(begin, 0) : end]
        step = n % settings["steps_per_loop"] + 1
        if len(span) < end - begin or not span.max():
            durations.setdefault(step, []).append(None)
            continue
        loud = np.flatnonzero(span > settings["threshold_fraction_of_step_peak"] * span.max())
        durations.setdefault(step, []).append(float((loud[-1] - loud[0] + 1) / rate * 1000))
    return {"first_onset_seconds": first / rate}, durations


def decide(durations, expected_ms, settings=SETTINGS):
    """True when every step's median and at least 4 of 5 loops sit within tolerance."""
    tolerance = settings["tolerance_ms"]
    rows = {}
    for step, target in enumerate(expected_ms, 1):
        values = durations.get(step, [])
        usable = [v for v in values if v is not None]
        median = float(np.median(usable)) if usable else None
        close = sum(abs(v - target) <= tolerance for v in usable)
        rows[step] = {
            "expected_ms": target,
            "median_ms": median,
            "loop_ms": values,
            "holds": median is not None
            and abs(median - target) <= tolerance
            and close >= settings["min_agreeing_loops"],
        }
    return {"steps": rows, "holds": all(row["holds"] for row in rows.values())}
