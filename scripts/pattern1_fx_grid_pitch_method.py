"""Frozen per-note pitch method for dense patterns, with onsets taken from the step grid.

Developed for 16 notes per loop at 60 BPM (250 ms steps, 210 ms notes). The earlier
multi-step method found onsets by a fixed minimum gap, which fires inside a note when
notes are this close. Here the first note's onset is found on a smoothed envelope, every
later step's onset is predicted on the step grid, and each prediction is refined to the
envelope's rising edge within the step tolerance. The per-note classification is the
frozen step-1 rule, unchanged: within 20..130 ms after onset, "effect" when the pitch
reaches 10% above the reference, "none" when it stays within 1%.
"""

import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, sosfiltfilt

from scripts.pattern1_fx_step_pitch_method import SETTINGS as STEP1_SETTINGS

SETTINGS = {
    **STEP1_SETTINGS,
    "step_seconds": 0.25,
    "steps_per_loop": 16,
    "step_tolerance_seconds": 0.03,
    "envelope_window_seconds": 0.003,
    "note_track_seconds": 0.2,
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


def note_tracks(path, settings=SETTINGS):
    samples, rate = sf.read(str(path), always_2d=True)
    mono = samples.mean(axis=1)
    sos = butter(4, settings["band_hz"], btype="band", fs=rate, output="sos")
    mono = sosfiltfilt(sos, mono)
    envelope = maximum_filter1d(
        np.abs(mono), max(1, round(settings["envelope_window_seconds"] * rate))
    )
    peak = envelope.max()
    above = envelope > settings["onset_fraction_of_peak"] * peak
    rising = np.flatnonzero(above[1:] & ~above[:-1]) + 1
    if above[0]:
        rising = np.r_[0, rising]
    if not len(rising):
        raise ValueError("No sound found in the playback recording")
    first = int(rising[0])
    step = settings["step_seconds"] * rate
    tolerance = settings["step_tolerance_seconds"] * rate
    window = round(settings["window_seconds"] * rate)
    hop = round(settings["hop_seconds"] * rate)
    total = settings["loops"] * settings["steps_per_loop"]
    notes, missing = [], []
    for n in range(total):
        expected = first + n * step
        near = rising[np.abs(rising - expected) <= tolerance]
        if not len(near):
            missing.append(n)
            continue
        onset = int(near[np.argmin(np.abs(near - expected))])
        if onset + round(settings["note_track_seconds"] * rate) > len(mono):
            missing.append(n)
            continue
        hz, amp = [], []
        for start in range(0, round(settings["note_track_seconds"] * rate), hop):
            segment = mono[onset + start : onset + start + window]
            hz.append(_pitch(segment, rate, settings))
            amp.append(float(np.abs(segment).max() / peak))
        notes.append(
            {
                "onset_seconds": onset / rate,
                "offset_from_grid_ms": (onset - expected) / rate * 1000,
                "loop": n // settings["steps_per_loop"],
                "step": n % settings["steps_per_loop"] + 1,
                "hz": hz,
                "relative_amplitude": amp,
            }
        )
    times = [round(i * settings["hop_seconds"] * 1000, 1) for i in range(len(notes[0]["hz"]))]
    return {"times_ms": times, "notes": notes, "missing_grid_positions": missing}
