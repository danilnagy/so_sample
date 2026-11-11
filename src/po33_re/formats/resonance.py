"""Observed-code uniform Sound3/P1 resonance editing at cutoff16/pitch14/volume36."""

from .packets import calibrated_nonzero_reference
from .patterns import _replace_pattern_data, pattern_data
from .volume import CALIBRATED_SOUND3_KEYS_BY_STEP

CALIBRATED_SOUND3_RESONANCE_CODES = frozenset((0, 32, 63))


def calibrated_sound3_resonances(frame):
    """Read only tested uniform states or the earlier note32/parameter0 layout."""
    _, start, end, _ = calibrated_nonzero_reference(frame, 3)
    if (start, end) != (11716, 19716):
        raise ValueError("Resonance requires the tested Sound3 window11716..19716")
    data = pattern_data(frame, 1)
    values, legacy = [], []
    for step in range(1, 17):
        p, a = 48 * (step - 1) + 6, 768 + 16 * (step - 1) + 2
        key = CALIBRATED_SOUND3_KEYS_BY_STEP.get(step, 0)
        cutoff = (data[p + 1] >> 4) | ((data[p + 2] & 3) << 4)
        volume = (data[p] >> 6) | ((data[p + 1] & 15) << 2)
        value = data[p + 2] >> 2
        if (
            data[p] & 63 != 14
            or volume != 36
            or cutoff != 16
            or data[a] != key
            or value not in CALIBRATED_SOUND3_RESONANCE_CODES
        ):
            raise ValueError(
                "Unknown Sound3 resonance context: require cutoff16/pitch14/volume36 and tested note layout"
            )
        values.append(value)
        legacy.append(32 if key else 0)
    if len(set(values)) != 1 and values != legacy:
        raise ValueError(
            "Unknown Sound3 resonance automation: require uniform observed code or legacy note32/parameter0"
        )
    return tuple(values)


def set_calibrated_sound3_resonance(frame, value):
    """Set all16 third-primary high-six fields; preserve every nonresonance bit."""
    if type(value) is not int or value not in CALIBRATED_SOUND3_RESONANCE_CODES:
        raise ValueError("Resonance raw code must be an integer in {0,32,63}")
    calibrated_sound3_resonances(frame)
    data = bytearray(pattern_data(frame, 1))
    for step in range(16):
        p = 48 * step + 8
        data[p] = (data[p] & 3) | (value << 2)
    return _replace_pattern_data(frame, 1, bytes(data))
