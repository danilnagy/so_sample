"""Frozen per-note frequency method for the melodic keyboard scale map.

Notes are found on the 250 ms step grid with the per-note-gate tracks
(pattern1_fx_note_gate_method.py), using a wider band and search range because higher
keys play the sample faster: up to 26 semitones would put the tone near 5.4 kHz and the
note near 47 ms long. Each note's pitch is the median over windows 5..40 ms after its
onset whose amplitude is at least 20% of that note's own peak. A step's pitch is the
median over its first five loops, and intervals are in cents relative to step 1.
"""

import math

import numpy as np

from scripts.pattern1_fx_note_gate_method import SETTINGS as NOTE_GATE_SETTINGS
from scripts.pattern1_fx_note_gate_method import note_tracks

SETTINGS = {
    **NOTE_GATE_SETTINGS,
    "band_hz": [600.0, 8000.0],
    "search_hz": [900.0, 7500.0],
    "note_track_seconds": 0.1,
    "measure_window_ms": [5.0, 40.0],
    "min_measure_windows": 2,
    "cents_tolerance": 20.0,
}

MODELS = {
    "chromatic": [100 * k for k in range(16)],
    "major": [
        0,
        200,
        400,
        500,
        700,
        900,
        1100,
        1200,
        1400,
        1600,
        1700,
        1900,
        2100,
        2300,
        2400,
        2600,
    ],
    "natural_minor": [
        0,
        200,
        300,
        500,
        700,
        800,
        1000,
        1200,
        1400,
        1500,
        1700,
        1900,
        2000,
        2200,
        2400,
        2500,
    ],
}


def note_frequency(times, hz, amplitude, settings=SETTINGS):
    low, high = settings["measure_window_ms"]
    values = [
        f
        for t, f, a in zip(times, hz, amplitude)
        if low <= t <= high and a >= settings["min_relative_amplitude"]
    ]
    if len(values) < settings["min_measure_windows"]:
        return None
    return float(np.median(values))


def step_frequencies(path, settings=SETTINGS):
    tracks = note_tracks(path, settings)
    times = tracks["times_ms"]
    steps = {}
    for note in tracks["notes"]:
        if note["loop"] < settings["loops"]:
            freq = note_frequency(times, note["hz"], note["relative_amplitude"], settings)
            steps.setdefault(note["step"], []).append(freq)
    return tracks, steps


def intervals(steps):
    """Cents of each step's median pitch, and of each loop, relative to step 1."""
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


def decide(table, settings=SETTINGS, models=MODELS):
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
