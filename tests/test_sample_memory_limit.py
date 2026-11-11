from scripts.prepare_sample_memory_limit import (
    DURATION_MODEL_MS,
    LENGTH,
    SOUND16_CAPACITY,
    TOTAL,
    absolute_decision,
)


def test_limit_plan():
    assert TOTAL == 987136 == 917504 + SOUND16_CAPACITY
    assert -(-16 * LENGTH // 4096) * 4096 == SOUND16_CAPACITY
    assert abs(DURATION_MODEL_MS[0] - 181.33) < 0.01
    assert absolute_decision(800.0)["stored_rate"]
