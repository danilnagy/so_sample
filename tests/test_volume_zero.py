from scripts.prepare_volume_zero_test import VOLUME_CODES, decide_zero, predicted_nonzero_db

TABLE = {
    "3": -15.41,
    "9": -13.3,
    "21": -6.97,
    "27": -3.95,
    "36": 0.0,
    "45": 3.35,
    "54": 6.22,
    "63": 7.48,
}


def levels(zero_rule):
    predicted = predicted_nonzero_db(TABLE)
    by_step = {}
    for step in range(1, 17):
        if predicted[step - 1] is not None:
            by_step[step] = predicted[step - 1]
        else:
            by_step[step] = zero_rule(by_step[step - 1])
    return by_step, predicted


def test_hold_previous_is_recognised():
    by_step, predicted = levels(lambda previous: previous + 0.1)
    assert decide_zero(by_step, predicted)["classification"] == "hold_previous"


def test_fixed_default_is_recognised():
    by_step, predicted = levels(lambda previous: -7.5)
    assert decide_zero(by_step, predicted)["classification"] == "fixed_default"


def test_unreproduced_table_blocks_a_decision():
    by_step, predicted = levels(lambda previous: previous)
    by_step[3] += 2.0
    result = decide_zero(by_step, predicted)
    assert not result["table_reproduced"] and result["classification"] == "other_or_inconclusive"


def test_plan_alternates_measured_codes_with_zero():
    assert VOLUME_CODES[1::2] == [0] * 8
    assert all(str(c) in TABLE for c in VOLUME_CODES[0::2])
    assert predicted_nonzero_db(TABLE)[0] == 0
