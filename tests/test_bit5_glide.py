import numpy as np

from scripts.check_bit5_glide_test import evaluate
from scripts.prepare_bit5_glide_test import BITS, EXPECTED_HZ, PITCHES


def readings(glide_flagged):
    early, late, levels, durations = {}, {}, {}, {}
    for step in range(1, 17):
        target = EXPECTED_HZ[step]
        previous = EXPECTED_HZ[step - 1] if step > 1 else EXPECTED_HZ[16]
        glides = glide_flagged or not BITS[step - 1]
        start = target * (previous / target) ** 0.3 if glides else target
        early[step] = [start] * 5
        late[step] = [target] * 5
        levels[step] = 30.0
        durations[step] = (
            [180.0 if glides else 167.5] * 5 if PITCHES[step - 1] == 25 else [240.0] * 5
        )
    return early, late, levels, durations


def test_plan_alternates_and_flags_second_half():
    assert PITCHES[:4] == [7, 25, 7, 25] and BITS == [0] * 8 + [1] * 8
    assert np.isclose(EXPECTED_HZ[2] / EXPECTED_HZ[1], 2 ** (18 / 12))


def test_models_are_told_apart():
    assert evaluate(*readings(glide_flagged=True))["classification"] == "bit5_inert"
    assert evaluate(*readings(glide_flagged=False))["classification"] == "bit5_no_glide"
