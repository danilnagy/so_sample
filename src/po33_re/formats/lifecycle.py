"""Bounded sample lifecycle operations with matching local hardware evidence."""

from .packets import Packet, sound_data, sound_groups
from .patterns import pattern_data


def copy_calibrated_melodic_reference(frame, source_sound, destination_sound):
    """Copy the observed unshared Sound6 owner into empty Sound7 as a reference.

    Preserve all codes, source metadata, patterns and unknown packets. No backing
    allocation or arbitrary source/destination mapping is inferred.
    """
    if (
        type(source_sound) is not int
        or type(destination_sound) is not int
        or (source_sound, destination_sound) != (6, 7)
    ):
        raise ValueError("Only the hardware-validated Sound6-to7 reference copy is supported")
    groups = sound_groups(frame)
    if 6 not in groups or groups[6]:
        raise ValueError("Destination must be an existing empty selector")
    data = sound_data(frame, 5)
    if len(data) != 32777 or data[:9].hex() not in (
        "00000000c078000005",  # Earlier recorded/generated endpoint 30912.
        "00000000ab44000005",  # Hardware-accepted imported endpoint 17579.
    ):
        raise ValueError("Expected an observed zero-start self-owned 32768-code source layout")
    referrers = []
    for key, indices in groups.items():
        if not indices:
            continue
        record = sound_data(frame, key)
        if len(record) < 9 or record[8] == 6:
            raise ValueError("Malformed sample or reference to empty destination")
        if record[8] == 5:
            referrers.append(key)
    if referrers != [5]:
        raise ValueError("Source must currently be unshared")
    index = next(i for i, packet in enumerate(frame.packets) if packet == Packet(0x68B5, b"\x06"))
    return frame.packets[: index + 1] + (Packet(0xEF78, data[:9]),) + frame.packets[index + 1 :]


def delete_calibrated_melodic_sound(frame, sound_slot):
    """Only shared Sound6-to7 ownership transfer or unshared Sound7 removal.

    The full transferred buffer and packet geometry are preserved. Unsupported
    owners, windows and additional referrers are rejected without guessing policy.
    """
    if type(sound_slot) is not int or sound_slot not in (6, 7):
        raise ValueError("Only the observed Sound6/Sound7 deletion contexts are supported")
    for pattern in range(1, 17):
        raw = pattern_data(frame, pattern)
        for step in range(16):
            for affected in (5, 6):
                offset = 48 * step + 3 * affected
                if raw[offset : offset + 3] != bytes(3) or raw[768 + 16 * step + affected] != 0:
                    raise ValueError("Deletion with Sound6/Sound7 pattern events is unverified")
    groups = sound_groups(frame)
    selector = sound_slot - 1
    data = sound_data(frame, selector)
    # Both shared transfer and last-owner removal have separate physical controls
    # at these two endpoints; unobserved windows remain outside the public guard.
    endpoints = (30912, 17579)
    expected = tuple(bytes(4) + end.to_bytes(4, "little") + bytes([selector]) for end in endpoints)
    if len(data) != 32777 or data[:9] not in expected:
        raise ValueError("Expected an observed self-owned 32768-code deletion layout")
    indices = groups[selector]
    lengths = [len(frame.packets[i].payload) for i in indices]
    if indices != list(range(indices[0], indices[-1] + 1)) or lengths != (
        [255] * 16 + [25] + ([255] * 16 + [16]) * 7
    ):
        raise ValueError("Expected contiguous observed sample-page packet geometry")
    referrers = []
    for key, own_indices in groups.items():
        if own_indices:
            record = sound_data(frame, key)
            if len(record) < 9:
                raise ValueError("Malformed sample record")
            if record[8] == selector:
                referrers.append(key)
    packets = list(frame.packets)
    if sound_slot == 7:
        if referrers != [6] or 5 not in groups or groups[5]:
            raise ValueError("Sound7 must be unshared and Sound6 empty")
    else:
        if referrers != [5, 6] or len(groups.get(6, [])) != 1 or sound_data(frame, 6) != data[:9]:
            raise ValueError("Expected only the exact retained Sound7 reference")
        destination = groups[6][0]
        if destination <= indices[-1]:
            raise ValueError("Expected source before retained destination")
        chunks = [frame.packets[i] for i in indices]
        first = chunks[0]
        chunks[0] = Packet(first.tag, first.payload[:8] + b"\x06" + first.payload[9:])
        packets[destination : destination + 1] = chunks
    del packets[indices[0] : indices[-1] + 1]
    return tuple(packets)
