from scripts.prepare_drum_pitch_test import MODELS, PITCH_CODES, absolute_decision


def test_models():
    assert len(PITCH_CODES) == 16 and min(PITCH_CODES) == 1 and max(PITCH_CODES) == 25
    assert MODELS["semitone_per_code"][6] == 1200.0 and MODELS["semitone_per_code"][12] == -1200.0
    assert absolute_decision(800.0)["stored_rate"] and not absolute_decision(1198.6)["stored_rate"]
