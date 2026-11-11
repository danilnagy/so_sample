"""Read the observed1032-byte pattern layout without decoding note bitfields."""

import hashlib

from .packets import Packet

CALIBRATED_MELODIC_KEYS = (1, 2, 7, 16)
CALIBRATED_AUXILIARY_VALUES = tuple(0xF0 | (key - 1) for key in CALIBRATED_MELODIC_KEYS)


def pattern_groups(frame):
    groups, current = {}, None
    for index, packet in enumerate(frame.packets):
        if packet.tag == 0xA041:
            if len(packet.payload) != 1 or packet.payload[0] >= 16 or packet.payload[0] in groups:
                raise ValueError("Unexpected or duplicate pattern selector")
            current = packet.payload[0]
            groups[current] = []
        elif packet.tag == 0xC498:
            if current is None:
                raise ValueError("Pattern data has no preceding pattern selector")
            groups[current].append(index)
        elif packet.tag == 0x68B5:
            current = None
    if set(groups) != set(range(16)):
        raise ValueError("Expected all16 observed pattern selectors")
    return groups


def pattern_data(frame, pattern_slot):
    if type(pattern_slot) is not int or not 1 <= pattern_slot <= 16:
        raise ValueError("Pattern slot1..16 required")
    indices = pattern_groups(frame)[pattern_slot - 1]
    data = b"".join(frame.packets[i].payload for i in indices)
    if len(data) != 1032:
        raise ValueError("Only the observed1032-byte pattern layout is supported")
    return data


def _replace_pattern_data(frame, pattern_slot, data):
    if not isinstance(data, bytes) or len(data) != 1032:
        raise ValueError("Exactly1032 replacement pattern bytes required")
    pattern_data(frame, pattern_slot)  # Validate the original observed layout.
    packets, offset = list(frame.packets), 0
    for packet_index in pattern_groups(frame)[pattern_slot - 1]:
        packet = packets[packet_index]
        length = len(packet.payload)
        packets[packet_index] = Packet(packet.tag, data[offset : offset + length])
        offset += length
    if offset != len(data):
        raise ValueError("Pattern chunks do not cover the replacement")
    return tuple(packets)


def clone_step(frame, pattern_slot, source_step, target_steps):
    """Experimentally copy a single opaque event into completely empty steps.

    Copy both complete raw rows, preserving the source, footer and all other
    packets. Note bitfields and auxiliary values are retained without decoding.
    Only the locally observed one-cell primary/auxiliary source is supported.
    """
    if type(source_step) is not int or not 1 <= source_step <= 16:
        raise ValueError("Source step1..16 required")
    targets = tuple(target_steps)
    if (
        not targets
        or any(type(step) is not int or not 1 <= step <= 16 for step in targets)
        or len(set(targets)) != len(targets)
        or source_step in targets
    ):
        raise ValueError("Distinct target steps1..16, excluding the source, required")
    original = pattern_data(frame, pattern_slot)
    source_index = source_step - 1
    primary = original[48 * source_index : 48 * (source_index + 1)]
    auxiliary = original[768 + 16 * source_index : 768 + 16 * (source_index + 1)]
    primary_cells = [cell for cell in range(16) if any(primary[3 * cell : 3 * (cell + 1)])]
    auxiliary_cells = [cell for cell in range(16) if auxiliary[cell]]
    if len(primary_cells) != 1 or primary_cells != auxiliary_cells:
        raise ValueError("Only an observed single primary/auxiliary event cell is supported")
    data = bytearray(original)
    for step in targets:
        index = step - 1
        p, a = 48 * index, 768 + 16 * index
        if any(original[p : p + 48]) or any(original[a : a + 16]):
            raise ValueError(f"Target step{step} is occupied; no data will be overwritten")
        data[p : p + 48] = primary
        data[a : a + 16] = auxiliary
    return _replace_pattern_data(frame, pattern_slot, bytes(data))


def set_melodic_key(frame, pattern_slot, step, sound_slot, keyboard_key):
    """Experimental key1/2/7/16 edit for the calibrated single Sound3 cell.

    Only observed0df883 primary data andF0/F1/F6/FF auxiliary values are accepted.
    Other keys, sounds, upper-nibble meanings and primary bitfields remain untested.
    """
    if type(step) is not int or not 1 <= step <= 16:
        raise ValueError("Step1..16 required")
    if type(sound_slot) is not int or sound_slot != 3:
        raise ValueError("Only the locally calibrated melodic Sound3 is supported")
    if type(keyboard_key) is not int or keyboard_key not in CALIBRATED_MELODIC_KEYS:
        raise ValueError("Only calibrated keyboard keys1/2/7/16 are supported")
    original = pattern_data(frame, pattern_slot)
    p, a = 48 * (step - 1), 768 + 16 * (step - 1)
    primary, auxiliary = original[p : p + 48], original[a : a + 16]
    primary_cells = [cell for cell in range(16) if any(primary[3 * cell : 3 * (cell + 1)])]
    auxiliary_cells = [cell for cell in range(16) if auxiliary[cell]]
    if primary_cells != [2] or auxiliary_cells != [2]:
        raise ValueError("Expected exactly one matching Sound3 primary/auxiliary cell")
    if primary[6:9] != bytes.fromhex("0df883") or auxiliary[2] not in CALIBRATED_AUXILIARY_VALUES:
        raise ValueError(
            "Only the observed Sound3 note parameters and calibrated auxiliary values are supported"
        )
    data = bytearray(original)
    data[a + 2] = (auxiliary[2] & 0xF0) | (keyboard_key - 1)
    return _replace_pattern_data(frame, pattern_slot, bytes(data))


def _sound2_row_offsets(data, step, occupied):
    """Validate only the observed Sound2 cell and optional calibrated Sound3 neighbour."""
    p, a = 48 * (step - 1), 768 + 16 * (step - 1)
    primary, auxiliary = data[p : p + 48], data[a : a + 16]
    primary_cells = [cell for cell in range(16) if any(primary[3 * cell : 3 * (cell + 1)])]
    auxiliary_cells = [cell for cell in range(16) if auxiliary[cell]]
    if not occupied and (any(primary[3:6]) or auxiliary[1]):
        raise ValueError(f"Sound2 target at step{step} is occupied; no data will be overwritten")
    allowed = {1, 2} if occupied else {2}
    if primary_cells != auxiliary_cells or not set(primary_cells) <= allowed:
        raise ValueError("Only matching observed Sound2/Sound3 cells are supported")
    if 2 in primary_cells and (
        primary[6:9] != bytes.fromhex("0df883") or auxiliary[2] not in CALIBRATED_AUXILIARY_VALUES
    ):
        raise ValueError("Unobserved neighbouring Sound3 parameters")
    if occupied and (primary[3:6] != bytes.fromhex("0d2831") or auxiliary[1] != 0xF0):
        raise ValueError("Only the observed Sound2 primary0d2831 and auxiliaryF0 are supported")
    return p, a


def clone_sound_cell(frame, pattern_slot, sound_slot, source_step, target_steps):
    """Experimentally copy the observed Sound2 key1 cell, preserving Sound3.

    Source primary0d2831 and auxiliaryF0 are copied without interpreting their
    parameters. Only empty Sound2 destinations and the observed optional Sound3
    neighbour are supported. Other cells and parameters remain untested.
    """
    if type(sound_slot) is not int or sound_slot != 2:
        raise ValueError("Only the locally observed Sound2 cell can be copied")
    if type(source_step) is not int or not 1 <= source_step <= 16:
        raise ValueError("Source step1..16 required")
    targets = tuple(target_steps)
    if (
        not targets
        or any(type(step) is not int or not 1 <= step <= 16 for step in targets)
        or len(set(targets)) != len(targets)
        or source_step in targets
    ):
        raise ValueError("Distinct target steps1..16, excluding the source, required")
    original = pattern_data(frame, pattern_slot)

    source_p, source_a = _sound2_row_offsets(original, source_step, occupied=True)
    data = bytearray(original)
    for step in targets:
        p, a = _sound2_row_offsets(original, step, occupied=False)
        data[p + 3 : p + 6] = original[source_p + 3 : source_p + 6]
        data[a + 1] = original[source_a + 1]
    return _replace_pattern_data(frame, pattern_slot, bytes(data))


def remove_sound_cell(frame, pattern_slot, sound_slot, steps):
    """Experimentally clear only occupied, observed Sound2 cells, preserving neighbours."""
    if type(sound_slot) is not int or sound_slot != 2:
        raise ValueError("Only the locally observed Sound2 cell can be removed")
    selected = tuple(steps)
    if (
        not selected
        or any(type(step) is not int or not 1 <= step <= 16 for step in selected)
        or len(set(selected)) != len(selected)
    ):
        raise ValueError("Distinct removal steps1..16 required")
    original = pattern_data(frame, pattern_slot)
    data = bytearray(original)
    for step in selected:
        p, a = _sound2_row_offsets(original, step, occupied=True)
        data[p + 3 : p + 6] = bytes(3)
        data[a + 1] = 0
    return _replace_pattern_data(frame, pattern_slot, bytes(data))


def _drum10_note_context(frame, pattern_slot, sound_slot):
    """Require the locally observed Pattern1/Sound10 copied-window context."""
    from .drums import calibrated_drum_copy_destination

    if type(pattern_slot) is not int or pattern_slot != 1:
        raise ValueError("Only the locally observed drum-note Pattern1 is supported")
    if type(sound_slot) is not int or sound_slot != 10:
        raise ValueError("Only the locally observed Sound10 drum note is supported")
    _, start, end, _ = calibrated_drum_copy_destination(frame, 10, 1)
    if (start, end) != (4045, 6045):
        raise ValueError("Expected the accepted Sound10/key1 nonzero copied window")
    return pattern_data(frame, 1)


def _drum10_row_offsets(data, step, occupied):
    if type(step) is not int or not 1 <= step <= 16:
        raise ValueError("Step1..16 required")
    p, a = 48 * (step - 1), 768 + 16 * (step - 1)
    primary, auxiliary = data[p : p + 48], data[a : a + 16]
    cells = [cell for cell in range(16) if any(primary[3 * cell : 3 * cell + 3])]
    aux_cells = [cell for cell in range(16) if auxiliary[cell]]
    if not occupied and (any(primary[27:30]) or auxiliary[9]):
        raise ValueError(f"Sound10 target at step{step} is occupied; no data will be overwritten")
    if cells != aux_cells or not set(cells) <= ({1, 2, 9} if occupied else {1, 2}):
        raise ValueError("Only the observed Sound2/Sound3 neighbors and Sound10 note are supported")
    if 1 in cells and (primary[3:6].hex() != "0d2831" or auxiliary[1] != 0xF0):
        raise ValueError("Unobserved neighboring Sound2 parameters")
    if 2 in cells and (
        primary[6:9].hex() != "0df883" or auxiliary[2] not in CALIBRATED_AUXILIARY_VALUES
    ):
        raise ValueError("Unobserved neighboring Sound3 parameters")
    if occupied and (primary[27:30].hex() != "0df883" or auxiliary[9] != 0x10):
        raise ValueError("Only the observed Sound10 primary0df883/auxiliary10 cell is supported")
    return p, a


def clone_drum_cell(frame, pattern_slot, sound_slot, source_step, target_steps):
    """Copy only the observed opaque Sound10/key1 cell, preserving calibrated neighbors."""
    original = _drum10_note_context(frame, pattern_slot, sound_slot)
    source_p, source_a = _drum10_row_offsets(original, source_step, occupied=True)
    targets = tuple(target_steps)
    if (
        not targets
        or any(type(step) is not int or not 1 <= step <= 16 for step in targets)
        or len(set(targets)) != len(targets)
        or source_step in targets
    ):
        raise ValueError("Distinct target steps1..16, excluding the source, required")
    data = bytearray(original)
    for step in targets:
        p, a = _drum10_row_offsets(original, step, occupied=False)
        data[p + 27 : p + 30] = original[source_p + 27 : source_p + 30]
        data[a + 9] = original[source_a + 9]
    return _replace_pattern_data(frame, pattern_slot, bytes(data))


def remove_drum_cell(frame, pattern_slot, sound_slot, steps):
    """Clear occupied observed Sound10 cells without interpreting note parameters."""
    original = _drum10_note_context(frame, pattern_slot, sound_slot)
    selected = tuple(steps)
    if (
        not selected
        or any(type(step) is not int or not 1 <= step <= 16 for step in selected)
        or len(set(selected)) != len(selected)
    ):
        raise ValueError("Distinct removal steps1..16 required")
    data = bytearray(original)
    for step in selected:
        p, a = _drum10_row_offsets(original, step, occupied=True)
        data[p + 27 : p + 30], data[a + 9] = bytes(3), 0
    return _replace_pattern_data(frame, pattern_slot, bytes(data))


def patterns_report(frame):
    patterns = []
    for slot in range(1, 17):
        data = pattern_data(frame, slot)
        rows = []
        for step in range(16):
            primary = data[48 * step : 48 * (step + 1)]
            auxiliary = data[768 + 16 * step : 768 + 16 * (step + 1)]
            if any(primary) or any(auxiliary):
                rows.append(
                    {
                        "step": step + 1,
                        "primary_48_bytes_hex": primary.hex(),
                        "nonzero_12_byte_regions": [
                            {
                                "region_index": region,
                                "hex": primary[12 * region : 12 * (region + 1)].hex(),
                            }
                            for region in range(4)
                            if any(primary[12 * region : 12 * (region + 1)])
                        ],
                        "auxiliary_16_bytes_hex": auxiliary.hex(),
                        "nonzero_three_byte_cells": [
                            {
                                "cell_index": cell,
                                "candidate_sound_slot": cell + 1,
                                "primary_hex": primary[3 * cell : 3 * (cell + 1)].hex(),
                                "auxiliary_byte": auxiliary[cell],
                            }
                            for cell in range(16)
                            if any(primary[3 * cell : 3 * (cell + 1)]) or auxiliary[cell]
                        ],
                    }
                )
        patterns.append(
            {
                "pattern_slot": slot,
                "payload_bytes": len(data),
                "payload_sha256": hashlib.sha256(data).hexdigest(),
                "all_primary_and_auxiliary_bytes_zero": not any(data[:1024]),
                "nonzero_step_rows": rows,
                "opaque_footer_hex": data[1024:].hex(),
            }
        )
    return {
        "analysis_version": "observed-pattern-layout-0.2",
        "patterns": patterns,
        "limits": [
            "Only raw byte regions are reported; sound, pitch, volume, timing and effects are not decoded.",
            "A48-byte primary stride and16-byte auxiliary stride are supported by local controlled kicks.",
            "The12-byte regions and auxiliary entries retain their raw values; their general semantics remain unverified.",
            "Sound2/Sound3/Sound9/Sound10 controls support three primary bytes and one auxiliary byte per sound slot; other slots remain untested.",
        ],
    }


# Melodic notes. A cell is (step, sound): three primary bytes at 48*(step-1)+3*(sound-1)
# and one auxiliary byte at 768+16*(step-1)+(sound-1). For melodic sounds the auxiliary
# high nibble is F and the low nibble is key - 1. On Sound3, keys 1..16 were measured as
# rows of the 4x4 grid: 0,+1,+3,+4 / -7,-5,-4,-2 / -12,-11,-9,-8 / -19,-17,-16,-14
# semitones from key 1 (registered hardware test). The primary bytes hold the sound's
# recorded parameters; written notes copy them from an existing note of the same sound.
MELODIC_SOUNDS = range(1, 9)


def _cell_offsets(step, sound):
    return 48 * (step - 1) + 3 * (sound - 1), 768 + 16 * (step - 1) + (sound - 1)


def melodic_notes(frame, pattern_slot, sound_slot):
    """Return 16 entries, step 1 first: the key 1..16, or None for an empty cell."""
    if type(sound_slot) is not int or sound_slot not in MELODIC_SOUNDS:
        raise ValueError("Melodic sound 1..8 required")
    data = pattern_data(frame, pattern_slot)
    notes = []
    for step in range(1, 17):
        _primary, a = _cell_offsets(step, sound_slot)
        if data[a] == 0:
            notes.append(None)
        elif data[a] >> 4 == 0xF:
            notes.append((data[a] & 0xF) + 1)
        else:
            raise ValueError(f"Step {step}: auxiliary byte {data[a]:02X} is not a melodic note")
    return notes


def set_melodic_notes(frame, pattern_slot, sound_slot, keys, template_sound=None):
    """Write one melodic sound's 16 steps in one pattern; every other byte is preserved.

    Notes copy the primary bytes of the existing notes of ``template_sound`` (default: the
    same sound; any sound 1..16, as melodic and drum notes share the primary layout) in
    this pattern, which must all be identical. None clears a step's cell.
    """
    if type(sound_slot) is not int or sound_slot not in MELODIC_SOUNDS:
        raise ValueError("Melodic sound 1..8 required")
    template_sound = sound_slot if template_sound is None else template_sound
    if type(template_sound) is not int or not 1 <= template_sound <= 16:
        raise ValueError("Template sound must be 1..16")
    if not isinstance(keys, list) or len(keys) != 16:
        raise ValueError("Keys must be a list of 16 entries, step 1 first")
    for key in keys:
        if key is not None and (type(key) is not int or not 1 <= key <= 16):
            raise ValueError("Each step must be null or a key 1..16")
    melodic_notes(frame, pattern_slot, sound_slot)  # Rejects non-melodic auxiliary values.
    data = bytearray(pattern_data(frame, pattern_slot))
    template = _template(data, template_sound) if any(k is not None for k in keys) else None
    for step, key in enumerate(keys, 1):
        p, a = _cell_offsets(step, sound_slot)
        if key is None:
            data[p : p + 3], data[a] = bytes(3), 0
        else:
            data[p : p + 3], data[a] = template, 0xF0 | (key - 1)
    return _replace_pattern_data(frame, pattern_slot, bytes(data))


def _template(data, template_sound):
    """The one parameter set shared by the template sound's notes in this pattern."""
    templates = set()
    for step in range(1, 17):
        p, a = _cell_offsets(step, template_sound)
        if data[a] and any(data[p : p + 3]):
            templates.add(bytes(data[p : p + 3]))
    if len(templates) != 1:
        raise ValueError(
            "The pattern needs existing notes of the template sound with one identical set "
            "of parameters"
        )
    return templates.pop()


# Drum sounds 9..16. A drum note's auxiliary byte has high nibble 1 and low nibble key - 1:
# Sound10 keys 1 and 2 were recorded on the device as 0x10 and 0x11. Keys 3..16 follow the
# same rule as a registered hypothesis (drum-notes writer test); key k plays slice k.
DRUM_SOUNDS = range(9, 17)


def drum_notes(frame, pattern_slot, sound_slot):
    """Return 16 entries, step 1 first: the drum key 1..16, or None for an empty cell."""
    if type(sound_slot) is not int or sound_slot not in DRUM_SOUNDS:
        raise ValueError("Drum sound 9..16 required")
    data = pattern_data(frame, pattern_slot)
    notes = []
    for step in range(1, 17):
        _primary, a = _cell_offsets(step, sound_slot)
        if data[a] == 0:
            notes.append(None)
        elif data[a] >> 4 == 0x1:
            notes.append((data[a] & 0xF) + 1)
        else:
            raise ValueError(f"Step {step}: auxiliary byte {data[a]:02X} is not a drum note")
    return notes


def set_drum_notes(frame, pattern_slot, sound_slot, keys, template_sound):
    """Write one drum sound's 16 steps in one pattern; every other byte is preserved.

    Notes copy the primary bytes of the existing notes of ``template_sound`` (any sound
    1..16) in this pattern, which must all be identical. None clears a step's cell.
    """
    if type(sound_slot) is not int or sound_slot not in DRUM_SOUNDS:
        raise ValueError("Drum sound 9..16 required")
    if type(template_sound) is not int or not 1 <= template_sound <= 16:
        raise ValueError("Template sound must be 1..16")
    if not isinstance(keys, list) or len(keys) != 16:
        raise ValueError("Keys must be a list of 16 entries, step 1 first")
    for key in keys:
        if key is not None and (type(key) is not int or not 1 <= key <= 16):
            raise ValueError("Each step must be null or a key 1..16")
    drum_notes(frame, pattern_slot, sound_slot)  # Rejects non-drum auxiliary values.
    data = bytearray(pattern_data(frame, pattern_slot))
    template = _template(data, template_sound) if any(k is not None for k in keys) else None
    for step, key in enumerate(keys, 1):
        p, a = _cell_offsets(step, sound_slot)
        if key is None:
            data[p : p + 3], data[a] = bytes(3), 0
        else:
            data[p : p + 3], data[a] = template, 0x10 | (key - 1)
    return _replace_pattern_data(frame, pattern_slot, bytes(data))


def copy_pattern(frame, source_pattern, destination_pattern):
    """Copy every byte of one pattern (cells, auxiliary bytes and effects footer) to another."""
    for value in (source_pattern, destination_pattern):
        if type(value) is not int or not 1 <= value <= 16:
            raise ValueError("Patterns must be 1..16")
    if source_pattern == destination_pattern:
        raise ValueError("Source and destination patterns must differ")
    return _replace_pattern_data(frame, destination_pattern, pattern_data(frame, source_pattern))


def set_notes(frame, pattern_slot, sound_slot, keys, parameters):
    """Write one sound's 16 steps with explicit parameters instead of a template.

    ``parameters`` holds pitch, volume, filter and resonance codes (0 = no lock). Melodic
    sounds 1..8 get auxiliary 0xF0 | (key - 1) and drum sounds 9..16 get 0x10 | (key - 1).
    None clears a step's cell; every other byte is preserved.
    """
    from .notes import encode_parameters

    if type(sound_slot) is not int or not 1 <= sound_slot <= 16:
        raise ValueError("Sound 1..16 required")
    if not isinstance(keys, list) or len(keys) != 16:
        raise ValueError("Keys must be a list of 16 entries, step 1 first")
    for key in keys:
        if key is not None and (type(key) is not int or not 1 <= key <= 16):
            raise ValueError("Each step must be null or a key 1..16")
    if not isinstance(parameters, dict) or set(parameters) != {
        "pitch",
        "volume",
        "filter",
        "resonance",
    }:
        raise ValueError("Parameters must give pitch, volume, filter and resonance")
    primary = encode_parameters(bytes(3), **parameters)
    high = 0xF0 if sound_slot in MELODIC_SOUNDS else 0x10
    data = bytearray(pattern_data(frame, pattern_slot))
    for step, key in enumerate(keys, 1):
        p, a = _cell_offsets(step, sound_slot)
        if key is None:
            data[p : p + 3], data[a] = bytes(3), 0
        else:
            data[p : p + 3], data[a] = primary, high | (key - 1)
    return _replace_pattern_data(frame, pattern_slot, bytes(data))
