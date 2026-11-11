import numpy as np
import pytest
import soundfile as sf

from scripts.pattern1_key_scale_grid_method import SETTINGS, decide, intervals, step_frequencies
from scripts.prepare_pattern1_key_scale_map_rerun import MODELS, ROW_LAYOUT

RATE = 44100
BASE = 1190.417


def write_cut_notes(path, cents, loops=6, step_seconds=0.25):
    """Notes cut the previous one; low keys would otherwise ring past the next step."""
    step = round(step_seconds * RATE)
    loop = np.zeros(16 * step)
    for s, c in enumerate(cents, 1):
        ratio = 2 ** (c / 1200)
        length = min(round(0.21 / ratio * RATE), step)
        t = np.arange(length) / RATE
        loop[(s - 1) * step : (s - 1) * step + length] = 0.3 * np.sin(2 * np.pi * BASE * ratio * t)
    mono = np.r_[np.zeros(RATE), np.tile(loop, loops)]
    sf.write(path, np.column_stack((mono, mono)), RATE, subtype="PCM_16")


@pytest.mark.parametrize("model", list(MODELS))
def test_every_registered_model_is_recognised_with_cut_notes(tmp_path, model):
    write_cut_notes(tmp_path / "s.wav", MODELS[model])
    info, steps = step_frequencies(tmp_path / "s.wav", SETTINGS)
    assert info["missing"] == []
    table = intervals(steps)
    errors = [abs(table["steps"][s]["median_cents"] - MODELS[model][s - 1]) for s in range(1, 17)]
    assert max(errors) < 5
    assert decide(table, MODELS)["classification"] == model


def test_row_layout_reaches_the_lowest_keys(tmp_path):
    write_cut_notes(tmp_path / "s.wav", ROW_LAYOUT)
    table = intervals(step_frequencies(tmp_path / "s.wav", SETTINGS)[1])
    assert abs(table["steps"][13]["median_hz"] - BASE * 2 ** (-19 / 12)) < 1.5


def test_recording_that_starts_mid_note_is_rejected(tmp_path):
    t = np.arange(RATE) / RATE
    tone = 0.3 * np.sin(2 * np.pi * BASE * t)
    sf.write(tmp_path / "s.wav", np.column_stack((tone, tone)), RATE, subtype="PCM_16")
    with pytest.raises(ValueError, match="silence"):
        step_frequencies(tmp_path / "s.wav", SETTINGS)
