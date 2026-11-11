from scripts.check_sample_window_test import evaluate
from scripts.prepare_sample_window_test import (
    BOUNDARIES,
    EXPECTED_HZ,
    EXPECTED_MS,
    IGNORED_HZ,
    NATIVE_CODES,
    STEPS,
    WINDOWS,
    keys_for,
)


def test_geometry():
    assert BOUNDARIES[-1] == NATIVE_CODES and WINDOWS[6] == (11719, 17578)
    assert round(EXPECTED_HZ[6], 1) == 899.0 and round(EXPECTED_HZ[7], 1) == 749.2
    assert round(IGNORED_HZ, 1) == 599.3 and round(EXPECTED_MS, 1) == 166.8
    assert keys_for(6)[0] == 1 and keys_for(7)[2] == 1 and keys_for(6)[2] is None


def readings(honoured):
    steps, durations = {}, {}
    for slot, slot_steps in STEPS.items():
        for step in slot_steps:
            hz = EXPECTED_HZ[slot] if honoured else IGNORED_HZ
            steps[step] = [hz] * 5
            durations[step] = [EXPECTED_MS if honoured else 240.0] * 5
    return steps, durations


def test_models_are_told_apart():
    assert evaluate(*readings(True))["classification"] == "window_honoured"
    assert evaluate(*readings(False))["classification"] == "start_ignored"
