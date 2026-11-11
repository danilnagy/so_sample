"""Frozen per-note pitch method for patterns with notes on several steps.

Extends the frozen step-1 method (pattern1_fx_step_pitch_method.py), whose
classification is reused unchanged: within 20..130 ms after a note's onset, "effect"
when the pitch reaches 10% above the reference, "none" when it stays within 1%.

Notes are found as band-passed envelope onsets at least 0.3 s apart. Each onset is
assigned to a step from its time since the first onset (150 ms per step at 100 BPM);
onsets that do not land within 30 ms of a step are rejected. Loops are counted from
the first onset, 16 steps each. A step's result needs the median over its first five
loops and at least four of the five individual loops to agree.
"""

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

from scripts.pattern1_fx_step_pitch_method import SETTINGS as STEP1_SETTINGS
from scripts.pattern1_fx_step_pitch_method import classify_step1

SETTINGS = {
    **STEP1_SETTINGS,
    "min_note_gap_seconds": 0.3,
    "step_seconds": 0.15,
    "steps_per_loop": 16,
    "step_tolerance_seconds": 0.03,
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
    envelope = np.abs(mono)
    peak = envelope.max()
    above = np.flatnonzero(envelope > settings["onset_fraction_of_peak"] * peak)
    if not len(above):
        raise ValueError("No sound found in the playback recording")
    onsets = [int(above[0])]
    for index in above:
        if index - onsets[-1] > settings["min_note_gap_seconds"] * rate:
            onsets.append(int(index))
    window = round(settings["window_seconds"] * rate)
    hop = round(settings["hop_seconds"] * rate)
    first = onsets[0]
    notes, rejected = [], []
    for onset in onsets:
        elapsed = (onset - first) / rate
        position = elapsed / settings["step_seconds"]
        nearest = round(position)
        if abs(position - nearest) * settings["step_seconds"] > settings["step_tolerance_seconds"]:
            rejected.append(onset / rate)
            continue
        hz, amp = [], []
        for start in range(0, round(settings["note_track_seconds"] * rate), hop):
            segment = mono[onset + start : onset + start + window]
            if len(segment) < window:
                break
            hz.append(_pitch(segment, rate, settings))
            amp.append(float(np.abs(segment).max() / peak))
        notes.append(
            {
                "onset_seconds": onset / rate,
                "loop": nearest // settings["steps_per_loop"],
                "step": nearest % settings["steps_per_loop"] + 1,
                "hz": hz,
                "relative_amplitude": amp,
            }
        )
    times = [round(i * settings["hop_seconds"] * 1000, 1) for i in range(len(notes[0]["hz"]))]
    return {"times_ms": times, "notes": notes, "rejected_onsets_seconds": rejected}


def step_results(tracks, reference_hz, settings=SETTINGS):
    times = tracks["times_ms"]
    by_step = {}
    for note in tracks["notes"]:
        if note["loop"] < settings["loops"]:
            by_step.setdefault(note["step"], []).append(note)
    results = {}
    for step, notes in sorted(by_step.items()):
        length = min(len(note["hz"]) for note in notes)
        median_hz = np.median([note["hz"][:length] for note in notes], axis=0).tolist()
        median_amp = np.median(
            [note["relative_amplitude"][:length] for note in notes], axis=0
        ).tolist()
        results[step] = {
            "loops": len(notes),
            "median": classify_step1(times[:length], median_hz, median_amp, reference_hz, settings),
            "per_loop": [
                classify_step1(times, n["hz"], n["relative_amplitude"], reference_hz, settings)[
                    "class"
                ]
                for n in notes
            ],
        }
    return results


def decide(results, predictions, settings=SETTINGS):
    """A prediction holds when every listed step matches in its median and enough loops."""
    support = {}
    for model, expected in predictions.items():
        ok = set(expected) == {str(step) for step in results}
        for step, label in expected.items():
            result = results.get(int(step))
            ok = (
                ok
                and result is not None
                and result["median"]["class"] == label
                and sum(c == label for c in result["per_loop"]) >= settings["min_agreeing_loops"]
            )
        support[model] = ok
    supported = [model for model, ok in support.items() if ok]
    return {
        "model_support": support,
        "classification": supported[0] if len(supported) == 1 else "inconclusive",
    }
