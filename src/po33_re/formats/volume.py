"""Bounded uniform Sound3/Pattern1 recorded volume; raw six-bit codes only."""

from .packets import calibrated_nonzero_reference
from .patterns import _replace_pattern_data, pattern_data

CALIBRATED_SOUND3_KEYS_BY_STEP = {1: 0xF0, 2: 0xFF, 5: 0xF1, 9: 0xF6, 13: 0xFF}


def calibrated_sound3_volumes(frame):
    """Return all16 raw codes only within the physically tested sample/note context."""
    _, start, end, _ = calibrated_nonzero_reference(frame, 3)
    if (start, end) != (11716, 19716):
        raise ValueError("Volume requires the tested Sound3 window11716..19716")
    data = pattern_data(frame, 1)
    values = []
    for step in range(1, 17):
        p, a = 48 * (step - 1) + 6, 768 + 16 * (step - 1) + 2
        key = CALIBRATED_SOUND3_KEYS_BY_STEP.get(step, 0)
        expected = (13, 0xF0, 0x83) if key else (0, 0, 0)
        if (data[p] & 0x3F, data[p + 1] & 0xF0, data[p + 2]) != expected or data[a] != key:
            raise ValueError("Unknown Sound3 note/parameter layout outside volume mask")
        values.append((data[p] >> 6) | ((data[p + 1] & 15) << 2))
    return tuple(values)


def set_calibrated_sound3_volume(frame, value):
    """Set all16 tested Sound3/P1 cells uniformly; preserve every other byte/bit."""
    if type(value) is not int or not 0 <= value <= 63:
        raise ValueError("Volume raw code must be an integer from 0 to 63")
    calibrated_sound3_volumes(frame)
    data = bytearray(pattern_data(frame, 1))
    for step in range(16):
        p = 48 * step + 6
        data[p] = (data[p] & 0x3F) | ((value & 3) << 6)
        data[p + 1] = (data[p + 1] & 0xF0) | (value >> 2)
    return _replace_pattern_data(frame, 1, bytes(data))
