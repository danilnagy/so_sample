"""Research-only raw writers for fields whose meaning is still under test.

These bypass the semantic writers on purpose so an experiment can place arbitrary values.
They are not for editors; see docs/stray-bits-control.md for the experiment that uses them.
"""

from .packets import Packet
from .patterns import _cell_offsets, _replace_pattern_data, pattern_data


def set_raw_cell(frame, pattern_slot, step, sound_slot, primary_hex, auxiliary):
    """Write one pattern cell's 3 primary bytes and auxiliary byte verbatim."""
    if type(step) is not int or not 1 <= step <= 16:
        raise ValueError("Step 1..16 required")
    if type(sound_slot) is not int or not 1 <= sound_slot <= 16:
        raise ValueError("Sound 1..16 required")
    primary = bytes.fromhex(primary_hex)
    if len(primary) != 3:
        raise ValueError("Primary must be 3 bytes of hex")
    if type(auxiliary) is not int or not 0 <= auxiliary <= 255:
        raise ValueError("Auxiliary must be a byte")
    data = bytearray(pattern_data(frame, pattern_slot))
    p, a = _cell_offsets(step, sound_slot)
    data[p : p + 3], data[a] = primary, auxiliary
    return _replace_pattern_data(frame, pattern_slot, bytes(data))


def set_global_byte(frame, ordinal, offset, value):
    """Write one byte of the first (0) or second (1) 0x7d5c global record."""
    indices = [i for i, packet in enumerate(frame.packets) if packet.tag == 0x7D5C]
    if len(indices) != 2 or ordinal not in (0, 1):
        raise ValueError("Expected the two-global-record layout and ordinal 0 or 1")
    index = indices[ordinal]
    old = frame.packets[index].payload
    if type(offset) is not int or not 0 <= offset < len(old):
        raise ValueError(f"Offset must be 0..{len(old) - 1}")
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError("Value must be a byte")
    packets = list(frame.packets)
    packets[index] = Packet(0x7D5C, old[:offset] + bytes([value]) + old[offset + 1 :])
    return tuple(packets)
