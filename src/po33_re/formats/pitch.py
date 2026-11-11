"""Bounded uniform Sound3/P1 pitch at volume36; raw endpoint-bounded codes only."""

from .packets import calibrated_nonzero_reference
from .patterns import _replace_pattern_data, pattern_data
from .volume import CALIBRATED_SOUND3_KEYS_BY_STEP


def calibrated_sound3_pitches(frame):
    """Read the tested layout; zero is accepted only in unwritten parameter-only cells."""
    _, start, end, _ = calibrated_nonzero_reference(frame, 3)
    if (start, end) != (11716, 19716):
        raise ValueError("Pitch requires the tested Sound3 window11716..19716")
    data = pattern_data(frame, 1)
    values = []
    for step in range(1, 17):
        p, a = 48 * (step - 1) + 6, 768 + 16 * (step - 1) + 2
        key = CALIBRATED_SOUND3_KEYS_BY_STEP.get(step, 0)
        value = data[p] & 31
        volume = (data[p] >> 6) | ((data[p + 1] & 15) << 2)
        expected = (0xF0, 0x83) if key else (0, 0)
        if (
            data[p] & 32
            or volume != 36
            or (data[p + 1] & 0xF0, data[p + 2]) != expected
            or data[a] != key
            or not (1 <= value <= 25 or (not key and value == 0))
        ):
            raise ValueError(
                "Unknown Sound3 pitch context: require volume36 and tested note/parameter layout"
            )
        values.append(value)
    return tuple(values)


def set_calibrated_sound3_pitch(frame, value):
    """Set all16 Sound3/P1 cells uniformly; preserve bit5 and all nonpitch data."""
    if type(value) is not int or not 1 <= value <= 25:
        raise ValueError("Pitch raw code must be an integer from 1 to 25")
    calibrated_sound3_pitches(frame)
    data = bytearray(pattern_data(frame, 1))
    for step in range(16):
        p = 48 * step + 6
        data[p] = (data[p] & 224) | value
    return _replace_pattern_data(frame, 1, bytes(data))
