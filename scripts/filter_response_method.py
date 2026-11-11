"""Frozen method: filter response per step, from a steady sawtooth against bypass steps.

The first step's onset is the first rising edge after silence (15% of the peak of the
band-passed, 3 ms maximum-filtered envelope); every later step follows the step grid. For
each step, a Hann window from 60 to 220 ms after the grid onset is transformed, and the
amplitude of harmonic h of the fundamental is the spectral peak within 3 Hz of h * f0.

A step's response is 20 log10 of its harmonic amplitudes over the median amplitudes of
all bypass steps (filter code 63) in the same chain cycle. Each step is classified:
- silent: every harmonic is below -40 dB;
- low_pass: the mean response of the top band is at least 3 dB below the bottom band;
- high_pass: the mean response of the bottom band is at least 3 dB below the top band;
- flat: otherwise.
A step's -3 dB edge is the frequency of the first harmonic, from the passing side, whose
response falls 3 dB below the best response of that step.
"""

import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "band_hz": [100.0, 11000.0],
    "onset_fraction_of_peak": 0.15,
    "envelope_window_seconds": 0.003,
    "step_seconds": 0.25,
    "window_ms": [60.0, 220.0],
    "fft_size": 65536,
    "fundamental_hz": 200.0,
    "harmonics": 50,
    "peak_search_hz": 3.0,
    "bottom_band": [1, 3],
    "top_band": [40, 50],
    "type_margin_db": 3.0,
    "silent_db": -40.0,
    "edge_db": 3.0,
}


def harmonic_amplitudes(path, steps_total, settings=SETTINGS):
    """Return the first onset and an array [step, harmonic] of amplitudes."""
    samples, rate = sf.read(str(path), always_2d=True)
    mono = samples.mean(axis=1)
    sos = butter(4, settings["band_hz"], btype="band", fs=rate, output="sos")
    envelope = maximum_filter1d(
        np.abs(sosfiltfilt(sos, mono)), max(1, round(settings["envelope_window_seconds"] * rate))
    )
    above = envelope > settings["onset_fraction_of_peak"] * envelope.max()
    rising = np.flatnonzero(above[1:] & ~above[:-1]) + 1
    if above[0] or not len(rising):
        raise ValueError("The recording must start in silence before the first note")
    first = int(rising[0])
    size = settings["fft_size"]
    freqs = np.fft.rfftfreq(size, 1 / rate)
    f0, count = settings["fundamental_hz"], settings["harmonics"]
    begin_ms, end_ms = settings["window_ms"]
    amplitudes = np.full((steps_total, count), np.nan)
    for n in range(steps_total):
        onset = first + n * settings["step_seconds"] * rate
        begin, end = round(onset + begin_ms / 1000 * rate), round(onset + end_ms / 1000 * rate)
        segment = mono[begin:end]
        if len(segment) < end - begin:
            break
        spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment)), size))
        for h in range(1, count + 1):
            near = np.abs(freqs - h * f0) <= settings["peak_search_hz"]
            amplitudes[n, h - 1] = spectrum[near].max()
    return first / rate, amplitudes


def responses(amplitudes, codes, cycle_steps):
    """dB response of every step against the median bypass (code 63) amplitudes per cycle."""
    result = np.full(amplitudes.shape, np.nan)
    for start in range(0, len(codes), cycle_steps):
        cycle = range(start, min(start + cycle_steps, len(codes)))
        bypass = [n for n in cycle if codes[n] == 63 and not np.isnan(amplitudes[n]).any()]
        if not bypass:
            continue
        reference = np.median(amplitudes[bypass], axis=0)
        for n in cycle:
            result[n] = 20 * np.log10(amplitudes[n] / reference)
    return result


def classify(response, settings=SETTINGS):
    """Return the type and -3 dB edge (Hz) of one step's response across harmonics."""
    if np.isnan(response).any():
        return {"type": None, "edge_hz": None}
    if response.max() < settings["silent_db"]:
        return {"type": "silent", "edge_hz": None}
    low = response[settings["bottom_band"][0] - 1 : settings["bottom_band"][1]].mean()
    high = response[settings["top_band"][0] - 1 : settings["top_band"][1]].mean()
    margin = settings["type_margin_db"]
    f0 = settings["fundamental_hz"]
    best = response.max()
    below = response < best - settings["edge_db"]
    if high <= low - margin:
        order = range(len(response))
        kind = "low_pass"
    elif low <= high - margin:
        order = range(len(response) - 1, -1, -1)
        kind = "high_pass"
    else:
        return {"type": "flat", "edge_hz": None}
    passing = False
    for index in order:
        if not below[index]:
            passing = True
        elif passing:
            return {"type": kind, "edge_hz": float((index + 1) * f0)}
    return {"type": kind, "edge_hz": None}
