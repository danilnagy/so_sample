import numpy as np

from scripts.check_no_lock_test import evaluate
from scripts.prepare_no_lock_test import held_pairs, step_plan


def test_held_pairs_point_to_the_last_nonzero_step_of_the_same_pattern():
    plan = step_plan()
    pairs = held_pairs()
    assert len(plan) == 32
    assert (2, 1, "filter") in pairs and (3, 1, "filter") in pairs
    assert (18, 17, "resonance") in pairs  # Pattern2 step 3 holds step 2's 56
    assert all(plan[m][0] == plan[n][0] for n, m, _ in pairs)


def test_evaluation_on_synthetic_responses():
    plan = step_plan()
    response = np.zeros((32 * 2, 50))
    for c in range(2):
        for n, (p, _, f, r) in enumerate(plan):
            level = f if p == 1 else r
            response[c * 32 + n] = level / 10.0
    for c in range(2):
        for zero, locked, _ in held_pairs():
            response[c * 32 + zero] = response[c * 32 + locked]
    result = evaluate(response, 32)
    assert result["hypotheses"]["zero_holds_last_lock"]
    assert not result["hypotheses"]["zero_filter_is_off"]
