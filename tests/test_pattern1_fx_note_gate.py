import numpy as np
import soundfile as sf

from scripts.pattern1_fx_multi_step_pitch_method import decide, step_results
from scripts.pattern1_fx_note_gate_method import SETTINGS, note_tracks
from scripts.prepare_pattern1_fx_full_step_map import EFFECT_STEPS, PREDICTIONS

RATE = 44100
REFERENCE = 1190.417


def write_octave_pairs(path, loops=6, step_seconds=0.25):
    """First step of each effect pair ramps at full level; the second plays a quiet,
    half-length exact octave, as observed on the device."""
    step = round(step_seconds * RATE)
    loop = np.zeros(16 * step)
    for s in range(1, 17):
        if s in EFFECT_STEPS and s - 1 in EFFECT_STEPS:
            t = np.arange(round(0.105 * RATE)) / RATE
            tone = 0.05 * np.sin(2 * np.pi * 2 * REFERENCE * t)
        else:
            t = np.arange(round(0.21 * RATE)) / RATE
            rise = 0.45 if s in EFFECT_STEPS else 0.0
            ratio = 1 + rise * np.minimum(t, 0.15) / 0.15
            tone = 0.3 * np.sin(2 * np.pi * np.cumsum(REFERENCE * ratio) / RATE)
        loop[(s - 1) * step : (s - 1) * step + len(tone)] += tone
    mono = np.r_[np.zeros(RATE), np.tile(loop, loops)]
    sf.write(path, np.column_stack((mono, mono)), RATE, subtype="PCM_16")


def test_quiet_full_octave_notes_are_measured_with_the_per_note_gate(tmp_path):
    write_octave_pairs(tmp_path / "pairs.wav")
    tracks = note_tracks(tmp_path / "pairs.wav", SETTINGS)
    results = step_results(tracks, REFERENCE, SETTINGS)
    assert results[3]["median"]["class"] == "effect"
    assert results[3]["median"]["max_ratio"] > 1.9
    assert decide(results, PREDICTIONS, SETTINGS)["classification"] == (
        "sequential_high_nibble_first"
    )


def test_recording_peak_gate_would_have_skipped_them(tmp_path):
    from scripts.pattern1_fx_grid_pitch_method import SETTINGS as GRID
    from scripts.pattern1_fx_grid_pitch_method import note_tracks as grid_tracks

    write_octave_pairs(tmp_path / "pairs.wav")
    results = step_results(grid_tracks(tmp_path / "pairs.wav", GRID), REFERENCE, GRID)
    assert results[3]["median"]["class"] == "indeterminate"


def test_per_note_amplitudes_peak_at_one(tmp_path):
    write_octave_pairs(tmp_path / "pairs.wav")
    for note in note_tracks(tmp_path / "pairs.wav", SETTINGS)["notes"]:
        assert max(note["relative_amplitude"]) == 1.0
