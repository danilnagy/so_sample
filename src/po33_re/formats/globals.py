"""Bounded global edits supported by physical controls and generated hardware restores."""

import hashlib

from .packets import Packet

TEMPO_PRESETS = (80, 120, 140)
TEMPO_OFFSET = 129
MIN_TEMPO_BPM, MAX_TEMPO_BPM = 60, 240
SWING_OFFSET = 130
MIN_SWING, MAX_SWING = 0, 18
# Hashes identify the observed opaque records, masking only tempo and swing.
# They are layout guards, not a claim that other fields are understood.
FIRST_GLOBAL_SHA256 = "c800383bf6f80b6589f84e447bf67e6dd61f6ac0984e855ad82a2a4913318674"
MASKED_SECOND_GLOBAL_SHA256 = "d83b81391c75f06328262d1b487bc2cd96cda3064e4335688f52f17e9cf3c0f4"


def _calibrated_global_payload(frame):
    """Recognize opaque context while allowing the independently calibrated fields."""
    indices = [i for i, packet in enumerate(frame.packets) if packet.tag == 0x7D5C]
    if indices != [1, 2] or any(len(frame.packets[i].payload) != 255 for i in indices):
        raise ValueError("Expected the observed two-global-record layout")
    first, second = [frame.packets[i].payload for i in indices]
    masked = second[:TEMPO_OFFSET] + bytes(2) + second[SWING_OFFSET + 1 :]
    if (
        hashlib.sha256(first).hexdigest() != FIRST_GLOBAL_SHA256
        or hashlib.sha256(masked).hexdigest() != MASKED_SECOND_GLOBAL_SHA256
    ):
        raise ValueError("Unknown opaque global context prevents global editing")
    if not MIN_SWING <= second[SWING_OFFSET] <= MAX_SWING:
        raise ValueError("Unknown opaque global context: source swing is outside 0 to 18")
    return second


def calibrated_tempo_preset(frame):
    """Keep the original preset-only source contract for the preset API."""
    bpm = _calibrated_global_payload(frame)[TEMPO_OFFSET]
    if bpm not in TEMPO_PRESETS:
        raise ValueError("Source tempo is outside the three calibrated presets")
    return bpm


def calibrated_tempo(frame):
    """Read an integer tempo within the observed physical60-to240 range."""
    bpm = _calibrated_global_payload(frame)[TEMPO_OFFSET]
    if not MIN_TEMPO_BPM <= bpm <= MAX_TEMPO_BPM:
        raise ValueError("Source tempo is outside the calibrated 60 to 240 BPM range")
    return bpm


def set_calibrated_tempo(frame, bpm):
    """Edit only the verified byte within the documented and physically bounded range."""
    if type(bpm) is not int or not MIN_TEMPO_BPM <= bpm <= MAX_TEMPO_BPM:
        raise ValueError("Tempo must be an integer from 60 to 240 BPM")
    calibrated_tempo(frame)
    old = frame.packets[2].payload
    packets = list(frame.packets)
    packets[2] = Packet(0x7D5C, old[:TEMPO_OFFSET] + bytes([bpm]) + old[TEMPO_OFFSET + 1 :])
    return tuple(packets)


def set_calibrated_tempo_preset(frame, bpm):
    """Change only the observed BPM byte; retain all other packets literally."""
    if type(bpm) is not int or bpm not in TEMPO_PRESETS:
        raise ValueError("Tempo preset must be the integer 80, 120 or 140")
    calibrated_tempo_preset(frame)
    old = frame.packets[2].payload
    packets = list(frame.packets)
    packets[2] = Packet(0x7D5C, old[:TEMPO_OFFSET] + bytes([bpm]) + old[TEMPO_OFFSET + 1 :])
    return tuple(packets)


def calibrated_swing(frame):
    """Read the bounded numeric swing field without assuming percent or timer units."""
    data = _calibrated_global_payload(frame)
    if not MIN_TEMPO_BPM <= data[TEMPO_OFFSET] <= MAX_TEMPO_BPM:
        raise ValueError("Source tempo is outside the calibrated 60 to 240 BPM range")
    return data[SWING_OFFSET]


def set_calibrated_swing(frame, value):
    """Edit only swing within physical display bounds, preserving tempo and opaque bytes.

    Physical0/9/18 and generated6 ground this range policy. Intermediate integers
    are not individually hardware tested, and no timing-unit conversion is applied.
    """
    if type(value) is not int or not MIN_SWING <= value <= MAX_SWING:
        raise ValueError("Swing must be an integer from 0 to 18")
    calibrated_swing(frame)
    old = frame.packets[2].payload
    packets = list(frame.packets)
    packets[2] = Packet(0x7D5C, old[:SWING_OFFSET] + bytes([value]) + old[SWING_OFFSET + 1 :])
    return tuple(packets)


# Second global record bytes 0..127 hold the pattern chain, each entry a pattern counted
# from zero, and byte 128 holds the chain length (docs/pattern-chain-results.md). The
# selected pattern is a chain of one (docs/selected-pattern-results.md). Entries past the
# length can hold stale values and are left unchanged.
SELECTED_PATTERN_OFFSET = 0
CHAIN_LENGTH_OFFSET = 128
MAX_CHAIN_LENGTH = 128


def _second_global_index(frame):
    indices = [i for i, packet in enumerate(frame.packets) if packet.tag == 0x7D5C]
    if len(indices) != 2 or len(frame.packets[indices[1]].payload) != 255:
        raise ValueError("Expected the observed two-global-record layout")
    return indices[1]


def pattern_chain(frame):
    """Return the chain as patterns 1..16, first entry first."""
    data = frame.packets[_second_global_index(frame)].payload
    length = data[CHAIN_LENGTH_OFFSET]
    if not 1 <= length <= MAX_CHAIN_LENGTH:
        raise ValueError(f"Unexpected chain length {length}")
    entries = list(data[:length])
    if any(value > 15 for value in entries):
        raise ValueError("Unexpected chain entry")
    return [value + 1 for value in entries]


def set_pattern_chain(frame, patterns):
    """Write a chain of 1..128 patterns (each 1..16); every other byte is preserved."""
    if (
        not isinstance(patterns, list)
        or not 1 <= len(patterns) <= MAX_CHAIN_LENGTH
        or any(type(p) is not int or not 1 <= p <= 16 for p in patterns)
    ):
        raise ValueError("Chain must be a list of 1..128 patterns, each 1..16")
    pattern_chain(frame)  # Rejects an unexpected current layout.
    index = _second_global_index(frame)
    packets = list(frame.packets)
    old = bytearray(packets[index].payload)
    old[: len(patterns)] = bytes(p - 1 for p in patterns)
    old[CHAIN_LENGTH_OFFSET] = len(patterns)
    packets[index] = Packet(0x7D5C, bytes(old))
    return tuple(packets)


def selected_pattern(frame):
    """Return the first pattern of the chain, 1..16 (the selected pattern)."""
    return pattern_chain(frame)[0]


def set_selected_pattern(frame, pattern):
    """Select one pattern 1..16: a chain of one."""
    if type(pattern) is not int or not 1 <= pattern <= 16:
        raise ValueError("Pattern must be 1..16")
    return set_pattern_chain(frame, [pattern])


def swing(frame):
    """Return the swing byte 0..18 of the second global record."""
    value = frame.packets[_second_global_index(frame)].payload[SWING_OFFSET]
    if not MIN_SWING <= value <= MAX_SWING:
        raise ValueError(f"Unexpected swing byte {value}")
    return value


def set_swing(frame, value):
    """Set the swing byte 0..18 in any two-record global layout; every other byte is kept."""
    if type(value) is not int or not MIN_SWING <= value <= MAX_SWING:
        raise ValueError("Swing must be an integer from 0 to 18")
    swing(frame)
    index = _second_global_index(frame)
    packets = list(frame.packets)
    old = packets[index].payload
    packets[index] = Packet(0x7D5C, old[:SWING_OFFSET] + bytes([value]) + old[SWING_OFFSET + 1 :])
    return tuple(packets)


def tempo(frame):
    """Return the tempo byte of the second global record, BPM 60..240."""
    value = frame.packets[_second_global_index(frame)].payload[TEMPO_OFFSET]
    if not MIN_TEMPO_BPM <= value <= MAX_TEMPO_BPM:
        raise ValueError(f"Unexpected tempo byte {value}")
    return value


def set_tempo(frame, bpm):
    """Set the tempo byte in any two-record global layout; every other byte is kept."""
    if type(bpm) is not int or not MIN_TEMPO_BPM <= bpm <= MAX_TEMPO_BPM:
        raise ValueError(f"Tempo must be an integer from {MIN_TEMPO_BPM} to {MAX_TEMPO_BPM}")
    tempo(frame)
    index = _second_global_index(frame)
    packets = list(frame.packets)
    old = packets[index].payload
    packets[index] = Packet(0x7D5C, old[:TEMPO_OFFSET] + bytes([bpm]) + old[TEMPO_OFFSET + 1 :])
    return tuple(packets)
