from scripts.check_fx_rules_test import evaluate
from scripts.prepare_fx_rules_test import (
    CHAIN,
    HOLDS,
    KEY_HZ,
    effects_for,
    fx13_prediction,
    fx14_prediction,
    predictions,
)


def test_predictions():
    assert [fx14_prediction("loop_steps_before_hold", 7, s) for s in range(7, 13)] == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]
    assert [fx14_prediction("loop_power_of_two", 7, s) for s in range(7, 13)] == [3, 4, 1, 2, 3, 4]
    assert [fx14_prediction("restart_every_four", 3, s) for s in range(3, 7)] == [3, 4, 1, 2]
    assert [fx13_prediction("previous_on_third", s) for s in range(2, 9)] == [2, 2, 4, 5, 6, 6, 8]
    assert [fx13_prediction("two_earlier_on_third", s) for s in range(5, 9)] == [5, 6, 5, 8]
    table = predictions()
    assert set(table) == set(HOLDS) and table[1]["loop_steps_before_hold"][16] == 2
    assert effects_for(6) == [None] * 16 and effects_for(4) == [None] * 4 + [14] * 8 + [None] * 4


def synthetic(rule14, rule13):
    described = []
    table = predictions()
    for pattern in CHAIN:
        steps = []
        for step in range(1, 17):
            key = step
            if pattern in HOLDS:
                fx, start, end = HOLDS[pattern]
                if start <= step <= end:
                    key = table[pattern][rule14 if fx == 14 else rule13][step]
            windows = [{"hz": KEY_HZ[key - 1], "level_db": 0.0}] * 3
            steps.append({"windows": windows, "onsets": 1})
        described.append(steps)
    return described


def test_rules_are_identified():
    result = evaluate(synthetic("loop_power_of_two", "two_earlier_on_third"))
    assert result["classification"] == {"14": "loop_power_of_two", "13": "two_earlier_on_third"}
    result = evaluate(synthetic("loop_steps_before_hold", "previous_on_third"))
    assert result["classification"] == {"14": "loop_steps_before_hold", "13": "previous_on_third"}
