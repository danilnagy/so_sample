from scripts.fx_period_median_method import SETTINGS, period_ms
from scripts.prepare_fx_period_120_test import MODELS, TOLERANCE, effects_for, model_support


def test_mismatch_method_ignores_boundary_glitches():
    track = []
    for _ in range(12):
        track += [0.0] * 14 + [380.0] * 10 + [900.0]  # a 250 ms loop with one glitch window
    period, score = period_ms(track, SETTINGS)
    assert period == 250.0 and score <= 0.05
    assert period_ms([0.0] * 40 + [387.0] * 40 + [700.0] * 39, SETTINGS)[0] is None
    flat = ([0.0] * 24 + [900.0]) * 4 + [0.0] * 19  # a retrigger: flat pitch, glitch every 250 ms
    assert period_ms(flat, SETTINGS)[0] == 250.0


def test_models_and_support():
    assert MODELS["tempo_synced"][1] == 125.0 and MODELS["fixed_ms"][2] == 333.3
    synced = {fx: ms * (1 + TOLERANCE / 2) for fx, ms in MODELS["tempo_synced"].items()}
    assert model_support(synced) == {"tempo_synced": True, "fixed_ms": False}
    assert model_support({**MODELS["fixed_ms"]}) == {"tempo_synced": False, "fixed_ms": True}
    assert model_support({1: None}) == {"tempo_synced": False, "fixed_ms": False}
    assert effects_for(6) == [None] * 16 and effects_for(5)[4:] == [12] * 12
