from scripts.prepare_drum_kit_import_test import LENGTHS
from scripts.prepare_drum_kit_pages_test import (
    CAPACITIES,
    DURATION_MODEL_MS,
    FREQUENCIES,
    LENGTH,
    MODELS,
    absolute_decision,
)


def test_planned_capacities_restore_the_observed_total():
    assert CAPACITIES[11] == -(-sum(LENGTHS) // 4096) * 4096
    assert CAPACITIES[12] == -(-16 * LENGTH // 4096) * 4096
    assert 266240 - 102400 + CAPACITIES[11] + CAPACITIES[12] == 266240


def test_models():
    assert MODELS["sound12_key_k"][-1] == 1500.0 and FREQUENCIES[0] == 500.0
    assert abs(DURATION_MODEL_MS[0] - 101.33) < 0.01
    assert absolute_decision(500.5)["stored_rate"]
    assert not absolute_decision(560.0)["stored_rate"]
