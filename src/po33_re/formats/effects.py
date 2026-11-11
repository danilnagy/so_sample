"""Uniform observed Pattern1 effects in the exact calibrated global7 project."""

import hashlib

from .packets import encode_packets
from .patterns import _replace_pattern_data, pattern_data

CALIBRATED_PATTERN1_EFFECT_CODES = {"none": 15, "octave_up": 6, "octave_down": 7}
_CLEAR_CONTEXT_BODY = "3d3762e28817a2bccf83986539c889d1e74e70139b2313affcc3d56cc1bb370b"


def calibrated_pattern1_effect(frame):
    """Read one uniform known effect; reject unknown notes, globals, samples or ordering."""
    data = bytearray(pattern_data(frame, 1))
    footer = data[1024:]
    if len(set(footer)) != 1:
        raise ValueError("Mixed Pattern1 effects require unverified per-step ordering")
    names = {code | (code << 4): name for name, code in CALIBRATED_PATTERN1_EFFECT_CODES.items()}
    if footer[0] not in names:
        raise ValueError("Only uniform calibrated none/octave_up/octave_down effects supported")
    data[1024:] = bytes([0xFF]) * 8
    normalized = encode_packets(_replace_pattern_data(frame, 1, bytes(data)))
    if (
        encode_packets(frame.packets) != frame.encoded_body
        or hashlib.sha256(normalized).hexdigest() != _CLEAR_CONTEXT_BODY
    ):
        raise ValueError(
            "Unknown Pattern1 effect context: exact calibrated global7 project required"
        )
    return names[footer[0]]


def set_calibrated_pattern1_effect(frame, effect):
    """Change only eight footer bytes, preserving every other byte including global131."""
    if type(effect) is not str or effect not in CALIBRATED_PATTERN1_EFFECT_CODES:
        raise ValueError("Effect must be one of none, octave_up, octave_down")
    calibrated_pattern1_effect(frame)
    code = CALIBRATED_PATTERN1_EFFECT_CODES[effect]
    data = bytearray(pattern_data(frame, 1))
    data[1024:] = bytes([code | (code << 4)]) * 8
    return _replace_pattern_data(frame, 1, bytes(data))


# Per-step effects. Footer byte k holds step 2k+1 in its high nibble and step 2k+2 in
# its low nibble; each nibble stores FX key - 1, and F means no effect. The layout was
# confirmed by registered pitch-track tests on Pattern 1, and the codes by recording FX
# keys 1..15 into patterns 2..16 on the device.
NO_EFFECT_CODE = 0xF


def step_effects(frame, pattern_slot):
    """Return 16 entries, step 1 first: an FX key 1..15, or None for no effect."""
    footer = pattern_data(frame, pattern_slot)[1024:]
    codes = [nibble for byte in footer for nibble in (byte >> 4, byte & 0xF)]
    return [None if code == NO_EFFECT_CODE else code + 1 for code in codes]


def set_step_effects(frame, pattern_slot, effects):
    """Write one pattern's 16 per-step effects, changing only its eight footer bytes."""
    if not isinstance(effects, list) or len(effects) != 16:
        raise ValueError("Effects must be a list of 16 entries, step 1 first")
    for value in effects:
        if value is not None and (type(value) is not int or not 1 <= value <= 15):
            raise ValueError("Each step effect must be null or an FX key 1..15")
    codes = [NO_EFFECT_CODE if value is None else value - 1 for value in effects]
    data = bytearray(pattern_data(frame, pattern_slot))
    data[1024:] = bytes((codes[2 * k] << 4) | codes[2 * k + 1] for k in range(8))
    return _replace_pattern_data(frame, pattern_slot, bytes(data))
