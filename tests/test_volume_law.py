import math

import numpy as np
import pytest
import soundfile as sf

from scripts.pattern1_volume_gain_method import SETTINGS, decide, levels_db, step_levels
from scripts.prepare_volume_law_test import MODELS, VOLUME_CODES

RATE = 44100


def write_levels(path, db_by_step, loops=6):
    step = round(0.25 * RATE)
    t = np.arange(round(0.21 * RATE)) / RATE
    loop = np.zeros(16 * step)
    for s, db in enumerate(db_by_step, 1):
        if db is None:
            continue
        tone = 0.05 * 10 ** (db / 20) * np.sin(2 * np.pi * 1190.4 * t)
        loop[(s - 1) * step : (s - 1) * step + len(tone)] = tone
    mono = np.r_[np.zeros(RATE), np.tile(loop, loops)]
    sf.write(path, np.column_stack((mono, mono)), RATE, subtype="FLOAT")


@pytest.mark.parametrize("model", list(MODELS))
def test_each_registered_law_is_recognised(tmp_path, model):
    write_levels(tmp_path / "v.wav", MODELS[model])
    _info, steps = step_levels(tmp_path / "v.wav", SETTINGS)
    table = levels_db(steps)
    for step, expected in enumerate(MODELS[model], 1):
        if expected is not None:
            assert abs(table["steps"][step]["median_db"] - expected) < 0.2
    assert table["steps"][2]["median_db"] is None or table["steps"][2]["median_db"] < -45
    assert decide(table, MODELS)["classification"] == model


def test_models_follow_the_prior_measurements():
    ratio_18 = 10 ** (
        (
            MODELS["power_1p38"][VOLUME_CODES.index(18)]
            - MODELS["power_1p38"][VOLUME_CODES.index(21)]
        )
        / 20
    )
    assert abs(ratio_18 - 0.8189) < 0.03
    assert MODELS["db_linear_0p5"][VOLUME_CODES.index(0)] is None
    assert MODELS["power_1p38"][0] == 0


def test_a_different_curve_is_reported_not_forced(tmp_path):
    curve = [None if c == 0 else 40 * math.log10(c / 36) for c in VOLUME_CODES]
    write_levels(tmp_path / "v.wav", curve)
    table = levels_db(step_levels(tmp_path / "v.wav", SETTINGS)[1])
    assert decide(table, MODELS)["classification"] == "other_or_inconclusive"
