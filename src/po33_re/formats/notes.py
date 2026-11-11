"""Per-step note parameters stored in a cell's three primary bytes.

Each field was located by its own calibrated hardware experiments on Sound 3, Pattern 1,
and together they cover all 24 bits, low bit first:

    bits 0-4    pitch       observed device range 1..25; 13 to 14 measured as about 1 semitone
    bit 5       unknown     preserved unchanged
    bits 6-11   volume      1..63 set a level; 0 means none set: the step keeps the
                            previous step's volume (registered hardware test)
    bits 12-17  filter      0..63; 63 neutral, lower values low-pass, higher values high-pass
    bits 18-23  resonance   0..63

The cell's auxiliary byte (key and note on/off) is separate. Writing a parameter keeps
every other bit, including the unknown bit and the other fields.
"""

from .patterns import _replace_pattern_data, pattern_data

FIELDS = {
    "pitch": (0, 5, range(26)),  # 0 = no lock (docs/note-bits-control.md); 1..25 = -12..+12
    "volume": (6, 6, range(64)),
    "filter": (12, 6, range(64)),
    "resonance": (18, 6, range(64)),
}
UNKNOWN_BIT = 5


def decode_parameters(primary):
    """Decode three primary bytes into named fields, including the unknown bit."""
    if not isinstance(primary, bytes | bytearray) or len(primary) != 3:
        raise ValueError("Three primary bytes required")
    value = int.from_bytes(primary, "little")
    fields = {
        name: (value >> shift) & ((1 << width) - 1) for name, (shift, width, _) in FIELDS.items()
    }
    fields["unknown_bit5"] = (value >> UNKNOWN_BIT) & 1
    return fields


def encode_parameters(primary, **changes):
    """Return new primary bytes with the named fields changed and every other bit kept."""
    value = int.from_bytes(bytes(primary), "little")
    for name, new in changes.items():
        if name not in FIELDS:
            raise ValueError(f"Unknown note parameter {name!r}")
        shift, width, allowed = FIELDS[name]
        if type(new) is not int or new not in allowed:
            raise ValueError(f"{name} must be an integer in {allowed.start}..{allowed.stop - 1}")
        mask = ((1 << width) - 1) << shift
        value = (value & ~mask) | (new << shift)
    return value.to_bytes(3, "little")


def _cell_offsets(step, sound):
    return 48 * (step - 1) + 3 * (sound - 1), 768 + 16 * (step - 1) + (sound - 1)


def step_parameters(frame, pattern_slot, sound_slot):
    """Return 16 entries, step 1 first: decoded parameters of each note, or None if empty."""
    if type(sound_slot) is not int or not 1 <= sound_slot <= 16:
        raise ValueError("Sound 1..16 required")
    data = pattern_data(frame, pattern_slot)
    result = []
    for step in range(1, 17):
        p, a = _cell_offsets(step, sound_slot)
        result.append(decode_parameters(data[p : p + 3]) if data[a] else None)
    return result


def set_step_parameters(frame, pattern_slot, sound_slot, parameter, values, allow_empty=False):
    """Set one parameter on chosen steps of one sound; None keeps a step unchanged.

    Only steps that hold a note (nonzero auxiliary byte) can be written, unless
    ``allow_empty``: then an empty step gets a parameter-only cell (primary bytes with a
    zero auxiliary byte), the layout the device writes for a lock on a step without a note.
    """
    if parameter not in FIELDS:
        raise ValueError(f"Parameter must be one of {sorted(FIELDS)}")
    if type(sound_slot) is not int or not 1 <= sound_slot <= 16:
        raise ValueError("Sound 1..16 required")
    if not isinstance(values, list) or len(values) != 16:
        raise ValueError("Values must be a list of 16 entries, step 1 first")
    data = bytearray(pattern_data(frame, pattern_slot))
    for step, new in enumerate(values, 1):
        if new is None:
            continue
        p, a = _cell_offsets(step, sound_slot)
        if not data[a] and not allow_empty:
            raise ValueError(f"Step {step} has no note for sound {sound_slot}")
        data[p : p + 3] = encode_parameters(data[p : p + 3], **{parameter: new})
    return _replace_pattern_data(frame, pattern_slot, bytes(data))


def unknown_bits(frame, pattern_slot, sound_slot):
    """Return 16 entries, step 1 first: bit 5 of each note's primary bytes, or None if empty."""
    data = pattern_data(frame, pattern_slot)
    result = []
    for step in range(1, 17):
        p, a = _cell_offsets(step, sound_slot)
        value = int.from_bytes(data[p : p + 3], "little")
        result.append((value >> UNKNOWN_BIT) & 1 if data[a] else None)
    return result


def set_unknown_bits(frame, pattern_slot, sound_slot, values):
    """Set bit 5 of chosen notes' primary bytes (research only); None keeps a step unchanged."""
    if type(sound_slot) is not int or not 1 <= sound_slot <= 16:
        raise ValueError("Sound 1..16 required")
    if not isinstance(values, list) or len(values) != 16:
        raise ValueError("Values must be a list of 16 entries, step 1 first")
    data = bytearray(pattern_data(frame, pattern_slot))
    for step, new in enumerate(values, 1):
        if new is None:
            continue
        if new not in (0, 1):
            raise ValueError("Each value must be null, 0 or 1")
        p, a = _cell_offsets(step, sound_slot)
        if not data[a]:
            raise ValueError(f"Step {step} has no note for sound {sound_slot}")
        value = int.from_bytes(data[p : p + 3], "little")
        value = (value & ~(1 << UNKNOWN_BIT)) | (new << UNKNOWN_BIT)
        data[p : p + 3] = value.to_bytes(3, "little")
    return _replace_pattern_data(frame, pattern_slot, bytes(data))
