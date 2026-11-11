from itertools import pairwise

from scripts.check_voice_release_test import evaluate
from scripts.prepare_voice_release_test import (
    JUDGED_STEPS,
    LONG,
    PREDICTIONS,
    REMAINING_MS,
    SOLO_STEPS,
    VOICE_HZ,
    VOICE_NAMES,
    keys_and_pitches,
    voice,
)


def test_plan_geometry():
    assert [round(x) for x in REMAINING_MS] == [417, 222, 84, -14]
    assert round(VOICE_HZ[LONG], 1) == 200.0 and len(VOICE_HZ) == 14
    spacing = sorted(VOICE_HZ.values())
    assert min(b - a for a, b in pairwise(spacing)) > 25
    assert set(SOLO_STEPS.values()) <= set(range(1, 17)) and len(SOLO_STEPS) == 14
    keys, pitches = keys_and_pitches(3, 2)
    assert keys[1] == 1 and pitches[1] == 1 and keys[5] == 1 and pitches[5] == 7
    keys, pitches = keys_and_pitches(3, 1)
    assert keys[0] == 13 and pitches[0] == 13 and keys[4] == 13
    keys, pitches = keys_and_pitches(2, 5)
    assert keys[3] == 1 and pitches[3] == 13
    assert PREDICTIONS["release_under_100ms"][11][voice(5)] is True
    assert PREDICTIONS["release_under_100ms"][3][voice(5)] is False
    assert PREDICTIONS["steal_nearest_end"][3][voice(4, 1)] is False


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
