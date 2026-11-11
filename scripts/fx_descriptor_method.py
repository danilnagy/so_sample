"""Frozen method: describe what a step sounds like across the step and the step after it.

For each note step the band-passed signal (150 to 6000 Hz) is examined from the step's
grid onset over the next 460 ms. The description is:
- onsets: rising crossings of the 3 ms maximum-filtered envelope above 15% of the note's
  peak, at least 25 ms apart;
- per 40 ms window: the level in dB against the loudest window of the control step, and
  the dominant frequency between 150 and 6000 Hz, with its height above the second peak.
The first grid onset is the first rising crossing above 15% of the whole recording's peak
after the first 20 ms; later steps follow the grid.
"""

import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "band_hz": [150.0, 6000.0],
    "envelope_window_seconds": 0.003,
    "skip_seconds": 0.02,
    "onset_fraction": 0.15,
    "refractory_seconds": 0.025,
    "fft_size": 32768,
    "min_level_db": -40.0,
}


def _prepare(path, settings):
    samples, rate = sf.read(str(path), always_2d=True)
    sos = butter(4, settings["band_hz"], btype="band", fs=rate, output="sos")
    mono = sosfiltfilt(sos, samples.mean(axis=1))
    envelope = maximum_filter1d(
        np.abs(mono), max(1, round(settings["envelope_window_seconds"] * rate))
    )
    envelope[: round(settings["skip_seconds"] * rate)] = 0.0
    above = envelope > settings["onset_fraction"] * envelope.max()
    rising = np.flatnonzero(above[1:] & ~above[:-1]) + 1
    if not len(rising):
        raise ValueError("No onset found")
    return mono, envelope, rate, int(rising[0]) / rate


def _dominant(segment, rate, settings):
    size = settings["fft_size"]
    spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment)), size))
    freqs = np.fft.rfftfreq(size, 1 / rate)
    band = (freqs >= settings["band_hz"][0]) & (freqs <= settings["band_hz"][1])
    idx = np.flatnonzero(band)
    s = spectrum[band]
    k = int(np.argmax(s))
    far = np.abs(freqs[idx] - freqs[idx[k]]) > 30
    second = s[far].max() if far.any() else 1e-12
    return float(freqs[idx[k]]), float(20 * np.log10(s[k] / (second + 1e-12)))


def describe(path, step_times, windows_ms, control_index, settings=SETTINGS):
    """step_times: list of grid onset seconds per described step; control_index picks the reference."""
    mono, envelope, rate, _first = _prepare(path, settings)
    raw = []
    for start in step_times:
        rows = []
        for begin_ms, end_ms in windows_ms:
            a, b = round((start + begin_ms / 1000) * rate), round((start + end_ms / 1000) * rate)
            segment = mono[a:b]
            if len(segment) < b - a:
                rows.append(None)
                continue
            freq, prominence = _dominant(segment, rate, settings)
            rows.append(
                {
                    "rms": float(np.sqrt(np.mean(segment**2))),
                    "hz": freq,
                    "prominence_db": prominence,
                }
            )
        raw.append(rows)
    reference = max(r["rms"] for r in raw[control_index] if r is not None)
    described = []
    for start, rows in zip(step_times, raw, strict=True):
        a = round(start * rate)
        b = round((start + windows_ms[-1][1] / 1000) * rate)
        env = envelope[a:b]
        peak = env.max() if len(env) else 0.0
        above = env > settings["onset_fraction"] * peak if peak else np.zeros(0, dtype=bool)
        rising = np.flatnonzero(above[1:] & ~above[:-1]) + 1
        if len(above) and above[0]:
            rising = np.r_[0, rising]  # already sounding at the grid onset
        onsets, last = [], -np.inf
        for index in rising:
            if index - last >= settings["refractory_seconds"] * rate:
                onsets.append(round(float(index / rate * 1000), 1))
                last = index
        described.append(
            {
                "onsets_ms": onsets,
                "windows": [
                    None
                    if r is None
                    else {
                        "level_db": float(20 * np.log10(r["rms"] / reference + 1e-12)),
                        "hz": r["hz"],
                        "prominence_db": r["prominence_db"],
                    }
                    for r in rows
                ],
            }
        )
    return described
