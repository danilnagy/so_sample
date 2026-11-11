import io

import numpy as np
import soundfile as sf

from scripts.check_swing_law_test import decide
from scripts.prepare_swing_law_test import CLICK_WINDOW, MODELS
from scripts.swing_onset_method import SETTINGS, onsets, summarize

RATE = 44100


def clicks(tmp_path, position):
    mono = np.zeros(int(22 * RATE))
    t = np.arange(int(0.05 * RATE)) / RATE
    click = 0.3 * np.sin(2 * np.pi * 900 * t) * np.exp(-t * 60)
    for loop in range(5):
        for step in range(16):
            time = 0.5 + (loop * 16 + step) * 0.25
            if step % 2:
                time += (position - 0.5) * 0.5
            start = int(time * RATE)
            mono[start : start + len(click)] += click
    path = tmp_path / "playback.wav"
    buffer = io.BytesIO()
    sf.write(buffer, np.column_stack((mono, mono)), RATE, subtype="FLOAT", format="WAV")
    path.write_bytes(buffer.getvalue())
    return path


def test_positions_are_recovered(tmp_path):
    for name, position in MODELS.items():
        summary = summarize(onsets(clicks(tmp_path, position), SETTINGS), SETTINGS)
        assert summary["loops_measured"] >= 4
        assert abs(summary["median_position"] - position) < 0.01
        assert decide(summary)["classification"] == name


def test_plan_constants():
    assert CLICK_WINDOW == (11719, 13719)
    assert round(MODELS["linear_in_code"], 3) == 0.873 or round(MODELS["linear_in_code"], 2) == 0.87
