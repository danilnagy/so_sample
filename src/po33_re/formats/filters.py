"""Bounded uniform Sound3/P1 FILTER edits using only observed literal codes."""

from .packets import calibrated_nonzero_reference
from .patterns import _replace_pattern_data, pattern_data
from .volume import CALIBRATED_SOUND3_KEYS_BY_STEP

CALIBRATED_SOUND3_FILTER_CODES = frozenset((1, 16, 52, 62, 63))


def calibrated_sound3_filters(frame):
    """Read only the tested pitch14/volume36 layout; zero means an unwritten cell only."""
    _, start, end, _ = calibrated_nonzero_reference(frame, 3)
    if (start, end) != (11716, 19716):
        raise ValueError("Filter requires the tested Sound3 window11716..19716")
    data = pattern_data(frame, 1)
    values = []
    for step in range(1, 17):
        p, a = 48 * (step - 1) + 6, 768 + 16 * (step - 1) + 2
        key = CALIBRATED_SOUND3_KEYS_BY_STEP.get(step, 0)
        value = (data[p + 1] >> 4) | ((data[p + 2] & 3) << 4)
        volume = (data[p] >> 6) | ((data[p + 1] & 15) << 2)
        if (
            data[p] & 63 != 14
            or volume != 36
            or data[p + 2] & 252 != (128 if key else 0)
            or data[a] != key
            or not (value in CALIBRATED_SOUND3_FILTER_CODES or (not key and value == 0))
        ):
            raise ValueError(
                "Unknown Sound3 filter context: require pitch14/volume36 and tested note/parameter layout"
            )
        values.append(value)
    return tuple(values)


def set_calibrated_sound3_filter(frame, value):
    """Set all16 Sound3/P1 cells; preserve every bit outside the strict FILTER masks."""
    if type(value) is not int or value not in CALIBRATED_SOUND3_FILTER_CODES:
        raise ValueError("Filter raw code must be an integer in {1,16,52,62,63}")
    calibrated_sound3_filters(frame)
    data = bytearray(pattern_data(frame, 1))
    for step in range(16):
        p = 48 * step + 6
        data[p + 1] = (data[p + 1] & 15) | ((value & 15) << 4)
        data[p + 2] = (data[p + 2] & 252) | (value >> 4)
    return _replace_pattern_data(frame, 1, bytes(data))
