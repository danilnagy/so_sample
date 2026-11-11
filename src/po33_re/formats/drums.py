"""Experimental edits limited to directly controlled Sound9/10 references."""

from .packets import Packet, sound_data, sound_groups

# Literal original-copy fields for selectors9..23; key2 has its own interval below.
# This is a local context guard, not an inferred general autoslice formula.
OTHER_SOUND9_FIELDS = (
    (4045, 8088),
    (8089, 12132),
    (12133, 16176),
    (16177, 20220),
    (20221, 24264),
    (24265, 28308),
    (28309, 32352),
    (32353, 36396),
    (36397, 40440),
    (40441, 44484),
    (44485, 48528),
    (48529, 52572),
    (52573, 56616),
    (56617, 60660),
    (60661, 64704),
)

# selector, fixed first field, measured minimum second field, observed maximum.
DRUM_SLICE_CALIBRATIONS = {1: (8, 0, 127, 4044), 2: (9, 4045, 4172, 8088)}


def calibrated_drum_slice(frame, sound_slot, slice_key):
    """Validate Sound9 keys1/2 at their observed starts and local endpoint bounds."""
    if type(sound_slot) is not int or sound_slot != 9:
        raise ValueError("Only the locally controlled drumSound9 is supported")
    if type(slice_key) is not int or slice_key not in DRUM_SLICE_CALIBRATIONS:
        raise ValueError("Only the directly controlled drum keys1/2 are supported")
    groups = sound_groups(frame)
    if any(len(groups.get(selector, [])) != 1 for selector in range(8, 24)):
        raise ValueError("Expected sixteen single-packet Sound9 references")
    for selector, start, minimum, maximum in DRUM_SLICE_CALIBRATIONS.values():
        data = sound_data(frame, selector)
        if (
            len(data) != 9
            or int.from_bytes(data[:4], "little") != start
            or data[8] != 0
            or not minimum <= int.from_bytes(data[4:8], "little") <= maximum
        ):
            raise ValueError("Drum keys1/2 differ from their observed fixed-start owner0 intervals")
    for selector, (first, second) in zip(range(10, 24), OTHER_SOUND9_FIELDS[1:]):
        expected = first.to_bytes(4, "little") + second.to_bytes(4, "little") + b"\0"
        if sound_data(frame, selector) != expected:
            raise ValueError(
                "Other fourteen Sound9 references differ from the observed copy context"
            )
    owner = sound_data(frame, 0)
    if len(owner) != 65545 or owner[:4] != bytes(4) or owner[8] != 0:
        raise ValueError("Expected the observed zero-start self-owned65536-code buffer")
    selector, start, _, _ = DRUM_SLICE_CALIBRATIONS[slice_key]
    end = int.from_bytes(sound_data(frame, selector)[4:8], "little")
    return groups[selector][0], start, end, owner


def replace_calibrated_drum_slice_end(frame, sound_slot, slice_key, endpoint):
    """Change only the second field of either fixed-start calibrated drum slice."""
    index, _, _, _ = calibrated_drum_slice(frame, sound_slot, slice_key)
    _, _, minimum, maximum = DRUM_SLICE_CALIBRATIONS[slice_key]
    if type(endpoint) is not int or not minimum <= endpoint <= maximum:
        raise ValueError("Integer drum endpoint in this key's local calibration interval required")
    packet = frame.packets[index]
    packets = list(frame.packets)
    packets[index] = Packet(
        packet.tag, packet.payload[:4] + endpoint.to_bytes(4, "little") + packet.payload[8:]
    )
    return tuple(packets)


def copy_calibrated_drum_slice(
    frame, source_sound, source_slice, destination_sound, destination_slice
):
    """Copy a Sound9 key1/2 reference into existing Sound10/key1 without allocation.

    The physical key1 copy and generated key2 copy have separate hardware evidence.
    Local source intervals and existing destination records still bound this writer.
    """
    source_index, _, _, _ = calibrated_drum_slice(frame, source_sound, source_slice)
    destination_index, _, _, _ = calibrated_drum_copy_destination(
        frame, destination_sound, destination_slice
    )
    packets = list(frame.packets)
    packets[destination_index] = Packet(
        frame.packets[destination_index].tag, frame.packets[source_index].payload
    )
    return tuple(packets)


def calibrated_drum_copy_destination(frame, destination_sound, destination_slice):
    """Validate the existing Sound10/key1 destination and retained local copy context."""
    if (
        type(destination_sound) is not int
        or destination_sound != 10
        or type(destination_slice) is not int
        or destination_slice != 1
    ):
        raise ValueError("Only the directly mapped destination Sound10/key1 is supported")
    _, _, _, owner = calibrated_drum_slice(frame, 9, 1)
    groups = sound_groups(frame)
    if any(len(groups.get(selector, [])) != 1 for selector in range(24, 40)):
        raise ValueError("Expected sixteen existing single-packet Sound10 references")
    for selector, (first, second) in zip(range(25, 40), OTHER_SOUND9_FIELDS):
        expected = first.to_bytes(4, "little") + second.to_bytes(4, "little") + b"\0"
        if sound_data(frame, selector) != expected:
            raise ValueError(
                "Other fifteen Sound10 references differ from the observed copy context"
            )
    destination = sound_data(frame, 24)
    if len(destination) != 9 or destination[8] != 0:
        raise ValueError("Expected an existing nine-byte owner0 Sound10/key1 reference")
    start, end = (
        int.from_bytes(destination[:4], "little"),
        int.from_bytes(destination[4:8], "little"),
    )
    if not any(
        start == observed_start and minimum <= end <= maximum
        for _, observed_start, minimum, maximum in DRUM_SLICE_CALIBRATIONS.values()
    ):
        raise ValueError("Destination reference lies outside the two local source-window contexts")
    return groups[24][0], start, end, owner
