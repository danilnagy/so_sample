"""Frozen method: one long note per pattern loop, its duration and the pitch of each quarter.

The first loop's onset is the first rising edge after silence (15% of the peak of the
band-passed, 3 ms maximum-filtered envelope); later loops follow the loop period. In each
loop, from its onset to 0.1 s before the next, the note sounds from the first to the last
sample above 10% of that span's peak. The pitch of quarter q is the dominant frequency
(parabolic peak) of a 50 ms Hann window centred at (q + 0.5) / 4 of the measured note.
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
    "loop_seconds": 4.0,
    "loops": 5,
    "tail_margin_seconds": 0.1,
    "threshold_fraction_of_loop_peak": 0.1,
    "quarters": 4,
    "window_seconds": 0.05,
    "fft_size": 65536,
    "duration_tolerance_ms": 10.0,
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


def measure(path, settings=SETTINGS):
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
    loop = settings["loop_seconds"] * rate
    half = round(settings["window_seconds"] * rate / 2)
    loops = []
    for n in range(settings["loops"]):
        begin = round(first + n * loop)
        end = round(first + (n + 1) * loop - settings["tail_margin_seconds"] * rate)
        span = envelope[begin:end]
        if len(span) < end - begin or not span.max():
            loops.append(None)
            continue
        loud = np.flatnonzero(span > settings["threshold_fraction_of_loop_peak"] * span.max())
        start, stop = begin + int(loud[0]), begin + int(loud[-1]) + 1
        quarters = []
        for q in range(settings["quarters"]):
            centre = round(start + (q + 0.5) / settings["quarters"] * (stop - start))
            quarters.append(_pitch(mono[centre - half : centre + half], rate, settings))
        loops.append({"duration_ms": (stop - start) / rate * 1000, "quarter_hz": quarters})
    return {"first_onset_seconds": first / rate}, loops


def decide(loops, expected_ms, expected_hz, settings=SETTINGS):
    usable = [entry for entry in loops if entry is not None]
    durations = [entry["duration_ms"] for entry in usable]
    duration_ok = (
        bool(durations)
        and abs(float(np.median(durations)) - expected_ms) <= settings["duration_tolerance_ms"]
        and sum(abs(d - expected_ms) <= settings["duration_tolerance_ms"] for d in durations)
        >= settings["min_agreeing_loops"]
    )
    quarters = []
    for q, target in enumerate(expected_hz):
        cents = [1200 * math.log2(entry["quarter_hz"][q] / target) for entry in usable]
        quarters.append(
            {
                "expected_hz": target,
                "median_cents_off": float(np.median(cents)) if cents else None,
                "holds": bool(cents)
                and abs(float(np.median(cents))) <= settings["cents_tolerance"]
                and sum(abs(c) <= settings["cents_tolerance"] for c in cents)
                >= settings["min_agreeing_loops"],
            }
        )
    return {
        "median_duration_ms": float(np.median(durations)) if durations else None,
        "duration_holds": duration_ok,
        "quarters": quarters,
        "pitch_holds": all(q["holds"] for q in quarters),
    }
