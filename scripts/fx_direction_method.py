"""Frozen method: which segment of a four-segment sample sounds through a long note.

Sound6's sample is four 0.25 s segments at 400, 500, 600 and 700 Hz, played 7 semitones up
at key 1 (599, 749, 899, 1049 Hz; 167 ms per segment, 667 ms in all). For each note the
band-passed signal is read in five 120 ms Hann windows starting 20, 190, 360, 530 and
700 ms after the grid onset, centred inside segments 1 to 4 and after the note.
Each window gives the dominant frequency, mapped to the nearest segment when its level is
within 30 dB of the reference window (the control's first note, first window), and the
onsets within 1.0 s of the note are counted as in the FX descriptor method.
"""

import math

import numpy as np

from scripts.fx_descriptor_method import _dominant, _prepare

SEGMENT_HZ = [400.0 * 2 ** (7 / 12) * k / 4 for k in (4, 5, 6, 7)]
SETTINGS = {
    "band_hz": [150.0, 6000.0],
    "envelope_window_seconds": 0.003,
    "skip_seconds": 0.02,
    "onset_fraction": 0.15,
    "refractory_seconds": 0.025,
    "fft_size": 32768,
    "window_starts_ms": [20.0, 190.0, 360.0, 530.0, 700.0],
    "window_ms": 120.0,
    "note_seconds": 1.0,
    "silence_db": -30.0,
}


def nearest_segment(hz):
    best = min(range(4), key=lambda k: abs(math.log2(hz / SEGMENT_HZ[k])))
    return best + 1, 1200 * math.log2(hz / SEGMENT_HZ[best])


def describe_notes(path, note_times, reference_index, settings=SETTINGS):
    mono, envelope, rate, _ = _prepare(path, settings)
    width = round(settings["window_ms"] / 1000 * rate)
    raw = []
    for start in note_times:
        windows = []
        for begin_ms in settings["window_starts_ms"]:
            a = round((start + begin_ms / 1000) * rate)
            segment = mono[a : a + width]
            if len(segment) < width:
                windows.append(None)
                continue
            hz, _ = _dominant(segment, rate, settings)
            windows.append({"rms": float(np.sqrt(np.mean(segment**2))), "hz": hz})
        a, b = round(start * rate), round((start + settings["note_seconds"] - 0.01) * rate)
        env = envelope[a:b]
        peak = env.max() if len(env) else 0.0
        above = env > settings["onset_fraction"] * peak if peak else np.zeros(0, dtype=bool)
        rising = np.flatnonzero(above[1:] & ~above[:-1]) + 1
        if len(above) and above[0]:
            rising = np.r_[0, rising]
        onsets, last = 0, -np.inf
        for index in rising:
            if index - last >= settings["refractory_seconds"] * rate:
                onsets += 1
                last = index
        raw.append({"windows": windows, "onsets": onsets})
    ref = raw[reference_index]["windows"][0]["rms"]
    notes = []
    for entry in raw:
        windows = []
        for w in entry["windows"]:
            if w is None:
                windows.append(None)
                continue
            level = float(20 * np.log10(w["rms"] / ref + 1e-12))
            segment, cents = nearest_segment(w["hz"])
            windows.append(
                {
                    "level_db": level,
                    "hz": w["hz"],
                    "segment": segment if level > settings["silence_db"] else None,
                    "cents_from_segment": cents,
                }
            )
        notes.append({"windows": windows, "onsets": entry["onsets"]})
    return notes
