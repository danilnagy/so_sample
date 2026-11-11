"""Exploratory variant of the polyphony method: the onset search skips the first 20 ms.

The frozen method failed on the polyphony playback because the band-pass filter leaves a
transient at sample 0 that exceeded the onset threshold. Only the onset search changes.

The first step's onset is the first sample where the band-passed, 3 ms maximum-filtered
envelope exceeds max(10 x the noise floor, 2% of the peak), the noise floor being the
median envelope of the first 200 ms; every later step follows the step grid. A peak-relative
threshold alone would miss a quiet solo note when a loud stack follows.
For each step, a Hann window from 100 to 240 ms after the grid onset is transformed and
each expected voice's level is the spectral peak within 12 Hz of its frequency. A voice
is present in a step when its level is within 10 dB of that voice's solo level, the
median over the solo steps in the same chain cycle.
"""

import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "band_hz": [150.0, 4000.0],
    "onset_noise_ratio": 10.0,
    "onset_min_fraction_of_peak": 0.02,
    "noise_floor_seconds": 0.2,
    "skip_seconds": 0.02,
    "envelope_window_seconds": 0.003,
    "step_seconds": 0.25,
    "window_ms": [100.0, 240.0],
    "fft_size": 65536,
    "peak_search_hz": 12.0,
    "presence_db": -10.0,
}


def voice_levels(path, steps_total, frequencies, settings=SETTINGS):
    """Return the first onset and an array [step, voice] of peak amplitudes."""
    samples, rate = sf.read(str(path), always_2d=True)
    mono = samples.mean(axis=1)
    sos = butter(4, settings["band_hz"], btype="band", fs=rate, output="sos")
    envelope = maximum_filter1d(
        np.abs(sosfiltfilt(sos, mono)), max(1, round(settings["envelope_window_seconds"] * rate))
    )
    skip = round(settings["skip_seconds"] * rate)
    envelope[:skip] = 0.0
    noise = np.median(envelope[skip : skip + round(settings["noise_floor_seconds"] * rate)])
    threshold = max(
        settings["onset_noise_ratio"] * noise,
        settings["onset_min_fraction_of_peak"] * envelope.max(),
    )
    above = envelope > threshold
    rising = np.flatnonzero(above[1:] & ~above[:-1]) + 1
    if above[0] or not len(rising):
        raise ValueError("The recording must start in silence before the first note")
    first = int(rising[0])
    size = settings["fft_size"]
    freqs = np.fft.rfftfreq(size, 1 / rate)
    begin_ms, end_ms = settings["window_ms"]
    levels = np.full((steps_total, len(frequencies)), np.nan)
    for n in range(steps_total):
        onset = first + n * settings["step_seconds"] * rate
        begin, end = round(onset + begin_ms / 1000 * rate), round(onset + end_ms / 1000 * rate)
        segment = mono[begin:end]
        if len(segment) < end - begin:
            break
        spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment)), size))
        for v, frequency in enumerate(frequencies):
            near = np.abs(freqs - frequency) <= settings["peak_search_hz"]
            levels[n, v] = spectrum[near].max()
    return first / rate, levels


def presence(levels, solo_steps, stack_steps, cycle_steps, settings=SETTINGS):
    """Per cycle and stack step (1-based within the cycle): dB of each voice against its
    solo level, and presence."""
    cycles = levels.shape[0] // cycle_steps
    result = []
    for c in range(cycles):
        base = c * cycle_steps
        solo = np.full(levels.shape[1], np.nan)
        for v, step in solo_steps.items():
            solo[v] = levels[base + step - 1, v]
        rows = {}
        for step in stack_steps:
            row = levels[base + step - 1]
            if np.isnan(row).any() or np.isnan(solo).any():
                rows[step] = None
                continue
            db = 20 * np.log10(row / solo)
            rows[step] = {
                "db_vs_solo": db.tolist(),
                "present": [bool(x >= settings["presence_db"]) for x in db],
            }
        result.append(rows)
    return result
