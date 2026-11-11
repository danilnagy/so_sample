from scripts.check_voice_steal_test import evaluate
from scripts.prepare_voice_steal_test import (
    JUDGED_STEPS,
    PREDICTIONS,
    SCENARIO_NOTES,
    VOICE_NAMES,
    keys_for,
    solo_notes,
)


def test_solo_and_scenario_keys():
    assert solo_notes()[1] == {1: 13} and solo_notes()[16] == {14: 1}
    assert keys_for(2, 1)[0] == 13 and keys_for(2, 1)[8] == 1 and keys_for(2, 8)[4] == 13
    assert keys_for(3, 8) == [None] * 8 + [13] + [None] * 3 + [13] + [None] * 3
    assert keys_for(3, 4)[1] == 1 and keys_for(3, 4)[14] == 1
    assert all(sum(1 for k in keys_for(3, s) if k) >= 1 for s in (1, 2, 3, 4, 5, 8, 11, 12, 14))
    assert SCENARIO_NOTES[15] == {1: 1, 2: 1, 3: 1, 4: 1}


def synthetic(model):
    cycles = []
    for _ in range(3):
        rows = {}
        for step in JUDGED_STEPS:
            expected = PREDICTIONS[model][step]
            present = [expected.get(name, False) for name in VOICE_NAMES]
            rows[16 + step] = {
                "present": present,
                "db_vs_solo": [0.0 if p else -40.0 for p in present],
            }
        cycles.append(rows)
    return cycles


def test_each_model_is_identified():
    for model in PREDICTIONS:
        result = evaluate(synthetic(model))
        assert result["classification"] == model, (model, result["model_support"])
