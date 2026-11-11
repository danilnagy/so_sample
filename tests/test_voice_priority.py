from scripts.check_voice_priority_test import evaluate
from scripts.prepare_polyphony_test import SOUND_ORDER
from scripts.prepare_voice_priority_test import RULES, STACKS, keys_for, predicted


def test_rules_disagree_somewhere_and_predict_four():
    for rule in RULES:
        assert all(len(predicted(rule, s)) == 4 for s in STACKS.values())
    assert predicted("drums_win", [1, 2, 3, 4, 11]) == [1, 2, 3, 11]
    assert predicted("lowest_sounds_win", [1, 2, 3, 4, 11]) == [1, 2, 3, 4]
    assert predicted("highest_sounds_win", [1, 2, 3, 4, 5]) == [2, 3, 4, 5]
    assert keys_for(11)[0] == 1 and keys_for(11)[2] is None


def synthetic_cycles(rule):
    cycles = []
    for _ in range(3):
        rows = {}
        for step, sounds in STACKS.items():
            present = predicted(rule, sounds)
            rows[16 + step] = {
                "db_vs_solo": [0.0 if s in present else -40.0 for s in SOUND_ORDER],
                "present": [s in present for s in SOUND_ORDER],
            }
        cycles.append(rows)
    return cycles


def test_evaluation_identifies_each_rule():
    for rule in RULES:
        result = evaluate(synthetic_cycles(rule))
        assert result["classification"] == rule and result["hypotheses"]["four_voices"]
