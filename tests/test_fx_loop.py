from scripts.check_fx_loop_test import classify
from scripts.prepare_fx_loop_test import HELD, HOLD_STEPS, effects_for, loop_prediction


def test_loop_predictions_and_classification():
    assert loop_prediction(16) == list(range(1, 17))
    assert loop_prediction(4)[:8] == [1, 2, 3, 4, 1, 2, 3, 4]
    assert loop_prediction(1) == [1] * 16
    for n in (1, 4, 8, 12, 16):
        assert classify(loop_prediction(n)) == f"loop_{n}"
    assert classify([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 9]) == "unresolved"
    assert classify([None] * 16) == "unresolved"


def test_effect_placement():
    assert effects_for(6) == [None] * 16
    assert effects_for(3) == [None] + [15] * 15 and HELD[3] == 15 and HOLD_STEPS[0] == 2
