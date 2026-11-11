from scripts.prepare_sample_memory_step2 import CAPACITIES, TOTAL, tone_wav


def test_step_total_and_tone():
    assert TOTAL == 815104 and TOTAL < 937500
    assert CAPACITIES == {11: 102400, 12: 102400, 6: 36864}
    assert len(tone_wav()) > 100000
