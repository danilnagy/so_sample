"""Grid note tracks with the audibility gate taken from each note's own peak.

The grid method (pattern1_fx_grid_pitch_method.py) gated windows at 20% of the whole
recording's peak. In the first full step map, notes under a fully engaged octave-up
effect played at about 0.16 of that peak, so they were skipped and read indeterminate.
Here each note's window amplitudes are divided by that note's own largest window, so a
quieter but clear note is still measured. Onsets, pitch tracking and the frozen
classification thresholds are otherwise unchanged.
"""

from scripts.pattern1_fx_grid_pitch_method import SETTINGS as GRID_SETTINGS
from scripts.pattern1_fx_grid_pitch_method import note_tracks as grid_note_tracks

SETTINGS = {**GRID_SETTINGS, "amplitude_gate_reference": "each_note_peak"}


def note_tracks(path, settings=SETTINGS):
    tracks = grid_note_tracks(path, settings)
    for note in tracks["notes"]:
        peak = max(note["relative_amplitude"]) or 1.0
        note["relative_amplitude_of_recording_peak"] = note["relative_amplitude"]
        note["relative_amplitude"] = [a / peak for a in note["relative_amplitude"]]
    return tracks
