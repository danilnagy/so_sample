"""Describe differences between two verified native frames in device terms.

Packets are grouped by their observed selectors: sound selector 0x68B5 owns the
following 0xEF78 data packets and pattern selector 0xA041 owns the following
0xC498 packets. Every other packet is an opaque record numbered by tag order.

Pattern data uses the observed 1032-byte layout: 16 steps x 16 sounds x 3 primary
bytes, then 16 x 16 auxiliary bytes, then an 8-byte footer. Cell differences are
reported raw. Field names are given only where they have hardware evidence, and
always as hints, never as decoded values.
"""

from collections import Counter

from ..formats.packets import END_TAG, START_TAG

SOUND_SELECTOR = 0x68B5
SOUND_DATA = 0xEF78
PATTERN_SELECTOR = 0xA041
PATTERN_DATA = 0xC498
PATTERN_BYTES = 1032
FOOTER_OFFSET = 1024
AUXILIARY_OFFSET = 768

# (tag, 1-based ordinal among packets with that tag, payload offset) -> name.
KNOWN_RECORD_BYTES = {
    (0x7D5C, 2, 129): "tempo_bpm",
    (0x7D5C, 2, 130): "swing",
    (0x7D5C, 2, 131): "opaque_global131",
}
MAX_BYTE_DIFFERENCES = 64


def sound_slot_hint(sound_id):
    """Map a zero-based sound selector id to a UI slot, marking what is verified."""
    if 0 <= sound_id < 8:
        return {"slot": sound_id + 1, "key": None, "verified": True}
    if 8 <= sound_id < 8 + 16 * 8:
        slot, key = 9 + (sound_id - 8) // 16, (sound_id - 8) % 16 + 1
        verified = slot == 9 or (slot == 10 and key == 1)
        return {"slot": slot, "key": key, "verified": verified}
    return {"slot": None, "key": None, "verified": False}


def regions(frame):
    """Group packet payloads into sound, pattern and opaque record regions."""
    result, current, ordinals = {}, None, Counter()
    for packet in frame.packets:
        if packet.tag in (START_TAG, END_TAG):
            continue
        if packet.tag in (SOUND_SELECTOR, PATTERN_SELECTOR) and len(packet.payload) == 1:
            kind = "sound" if packet.tag == SOUND_SELECTOR else "pattern"
            current = (kind, packet.payload[0])
            result.setdefault(current, b"")
            continue
        owned = (packet.tag == SOUND_DATA and current and current[0] == "sound") or (
            packet.tag == PATTERN_DATA and current and current[0] == "pattern"
        )
        if owned:
            result[current] += packet.payload
            continue
        ordinals[packet.tag] += 1
        result[("record", packet.tag, ordinals[packet.tag])] = packet.payload
    return result


def _byte_differences(old, new, name_for=None):
    shared = min(len(old), len(new))
    offsets = [i for i in range(shared) if old[i] != new[i]]
    items = []
    for offset in offsets[:MAX_BYTE_DIFFERENCES]:
        item = {"offset": offset, "old": old[offset], "new": new[offset]}
        name = name_for(offset) if name_for else None
        if name:
            item["name_hint"] = name
        items.append(item)
    return {
        "changed_byte_count": len(offsets),
        "lengths": [len(old), len(new)],
        "bytes": items,
        "bytes_truncated": len(offsets) > MAX_BYTE_DIFFERENCES,
    }


def _pattern_changes(number, old, new):
    changes = []
    for step in range(16):
        for cell in range(16):
            p = 48 * step + 3 * cell
            a = AUXILIARY_OFFSET + 16 * step + cell
            if old[p : p + 3] != new[p : p + 3] or old[a] != new[a]:
                item = {
                    "region": "pattern_cell",
                    "pattern": number + 1,
                    "step": step + 1,
                    "sound": cell + 1,
                    "primary": [old[p : p + 3].hex(), new[p : p + 3].hex()],
                    "auxiliary": [f"{old[a]:02x}", f"{new[a]:02x}"],
                }
                if not any(new[p : p + 3]) and not new[a]:
                    item["now_empty"] = True
                elif not any(old[p : p + 3]) and not old[a]:
                    item["was_empty"] = True
                changes.append(item)
    if old[FOOTER_OFFSET:] != new[FOOTER_OFFSET:]:
        changes.append(
            {
                "region": "pattern_footer",
                "pattern": number + 1,
                "footer": [old[FOOTER_OFFSET:].hex(), new[FOOTER_OFFSET:].hex()],
                "hint": "per-step effect nibbles; F is none, 6 octave up, 7 octave down",
            }
        )
    return changes


def _header_fields(data):
    if len(data) < 9:
        return None
    return {
        "start": int.from_bytes(data[0:4], "little"),
        "end": int.from_bytes(data[4:8], "little"),
        "owner": data[8],
    }


def _sound_change(sound_id, old, new):
    item = {"region": "sound", "sound_id": sound_id, "slot_hint": sound_slot_hint(sound_id)}
    old_header, new_header = _header_fields(old), _header_fields(new)
    if old[:9] != new[:9]:
        item["header"] = {"old": old_header, "new": new_header}
    old_codes, new_codes = old[9:], new[9:]
    if old_codes != new_codes:
        shared = min(len(old_codes), len(new_codes))
        changed = [i for i in range(shared) if old_codes[i] != new_codes[i]]
        item["sample_codes"] = {
            "lengths": [len(old_codes), len(new_codes)],
            "changed_in_overlap": len(changed),
            "first_changed_offset": changed[0] if changed else None,
            "last_changed_offset": changed[-1] if changed else None,
        }
    return item


def describe_changes(old_frame, new_frame):
    """Return a JSON-ready description of how new_frame differs from old_frame."""
    old_regions, new_regions = regions(old_frame), regions(new_frame)
    changes = []
    keys = sorted(set(old_regions) | set(new_regions), key=lambda k: (k[0], k[1:]))
    for key in keys:
        old, new = old_regions.get(key), new_regions.get(key)
        if old == new:
            continue
        if old is None or new is None:
            changes.append(
                {
                    "region": "added" if old is None else "removed",
                    "key": [key[0], *key[1:]],
                    "bytes": len(new if old is None else old),
                }
            )
            continue
        kind = key[0]
        if kind == "pattern" and len(old) == len(new) == PATTERN_BYTES:
            changes.extend(_pattern_changes(key[1], old, new))
        elif kind == "sound":
            changes.append(_sound_change(key[1], old, new))
        elif kind == "record":
            tag, ordinal = key[1], key[2]
            item = {"region": "record", "tag": f"0x{tag:04x}", "ordinal": ordinal}
            item.update(
                _byte_differences(
                    old,
                    new,
                    lambda offset, t=tag, n=ordinal: KNOWN_RECORD_BYTES.get((t, n, offset)),
                )
            )
            changes.append(item)
        else:
            item = {"region": kind, "key": [kind, *key[1:]]}
            item.update(_byte_differences(old, new))
            changes.append(item)
    return {
        "identical_body": old_frame.encoded_body == new_frame.encoded_body,
        "packet_counts": [len(old_frame.packets), len(new_frame.packets)],
        "change_count": len(changes),
        "changes": changes,
    }


def summarize_change(item):
    """One readable line for a change entry, for console output."""
    region = item["region"]
    if region == "pattern_cell":
        state = " (now empty)" if item.get("now_empty") else ""
        state = " (was empty)" if item.get("was_empty") else state
        return (
            f"Pattern {item['pattern']} step {item['step']} sound {item['sound']}: "
            f"primary {item['primary'][0]}->{item['primary'][1]}, "
            f"aux {item['auxiliary'][0]}->{item['auxiliary'][1]}{state}"
        )
    if region == "pattern_footer":
        return f"Pattern {item['pattern']} footer {item['footer'][0]}->{item['footer'][1]}"
    if region == "sound":
        hint = item["slot_hint"]
        name = f"sound id {item['sound_id']}"
        if hint["slot"]:
            name += f" (Sound {hint['slot']}" + (f" key {hint['key']}" if hint["key"] else "")
            name += ")" if hint["verified"] else ", unverified mapping)"
        parts = []
        if "header" in item:
            parts.append(f"header {item['header']['old']} -> {item['header']['new']}")
        if "sample_codes" in item:
            codes = item["sample_codes"]
            parts.append(
                f"sample codes {codes['lengths'][0]}->{codes['lengths'][1]}, "
                f"{codes['changed_in_overlap']} changed"
            )
        return f"{name}: " + "; ".join(parts)
    if region == "record":
        shown = ", ".join(
            f"byte {b['offset']}"
            + (f" ({b['name_hint']})" if "name_hint" in b else "")
            + f" {b['old']}->{b['new']}"
            for b in item["bytes"][:6]
        )
        more = (
            "" if item["changed_byte_count"] <= 6 else f" and {item['changed_byte_count'] - 6} more"
        )
        return f"Record {item['tag']} #{item['ordinal']}: {shown}{more}"
    if region in ("added", "removed"):
        return f"{region.capitalize()} region {item['key']} ({item['bytes']} bytes)"
    return f"{region}: {item.get('changed_byte_count', '?')} bytes changed"
