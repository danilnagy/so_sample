from scripts.check_priority_map_test import evaluate
from scripts.prepare_priority_map_test import RANKINGS, SOUND_ORDER, STACKS, keys_for, predicted


def test_rankings_disagree_on_the_sound11_stacks_only():
    differ = [
        s
        for s, sounds in STACKS.items()
        if predicted("lowest_sounds_win", sounds) != predicted("sound11_outranks_4_and_5", sounds)
    ]
    assert differ == [1, 13, 15]
    assert predicted("sound11_outranks_4_and_5", [2, 3, 4, 5, 11]) == [2, 3, 4, 11]
    assert keys_for(2, 11)[5] == 1 and keys_for(3, 11)[0] == 1 and keys_for(3, 12)[2] == 1


def synthetic(rule):
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


def test_each_ranking_is_identified():
    for rule in RANKINGS:
        result = evaluate(synthetic(rule))
        assert result["classification"] == rule and result["hypotheses"]["four_voices"]
