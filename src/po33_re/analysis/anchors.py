"""Bounded exact bit-anchor searches, retaining ambiguity and original offsets."""

import numpy as np

from .coding import validate_bits


def packed_offsets(bits):
    validate_bits(bits)
    return [np.packbits(bits[offset:], bitorder="little").tobytes() for offset in range(8)]


def find_anchor(needle, streams, target_count, limit=8):
    validate_bits(needle)
    if len(needle) < 8 or len(needle) % 8 or type(limit) is not int or limit < 1:
        raise ValueError("Anchor must contain complete bytes and limit must be positive")
    raw = np.packbits(needle, bitorder="little").tobytes()
    hits = []
    for offset, stream in enumerate(streams):
        start = 0
        for _ in range(limit + 1):
            found = stream.find(raw, start)
            if found < 0:
                break
            position = found * 8 + offset
            if position + len(needle) <= target_count:
                hits.append(position)
            start = found + 1
    hits = sorted(set(hits))
    return {"positions": hits[:limit], "more_than_limit": len(hits) > limit}


def extend_anchor(source, target, source_start, target_start, anchor_count, maximum=4096):
    validate_bits(source)
    validate_bits(target)
    if (
        type(maximum) is not int
        or maximum <= 0
        or type(anchor_count) is not int
        or anchor_count <= 0
    ):
        raise ValueError("Positive integer anchor and extension lengths required")
    if (
        source_start < 0
        or target_start < 0
        or source_start + anchor_count > len(source)
        or target_start + anchor_count > len(target)
    ):
        raise ValueError("Anchor outside arrays")
    if not np.array_equal(
        source[source_start : source_start + anchor_count],
        target[target_start : target_start + anchor_count],
    ):
        raise ValueError("Cannot extend a nonmatching anchor")
    backward = min(source_start, target_start, maximum)
    changes = np.flatnonzero(
        source[source_start - backward : source_start]
        != target[target_start - backward : target_start]
    )
    left = backward - int(changes[-1]) - 1 if len(changes) else backward
    sa, ta = source_start + anchor_count, target_start + anchor_count
    forward = min(len(source) - sa, len(target) - ta, maximum)
    changes = np.flatnonzero(source[sa : sa + forward] != target[ta : ta + forward])
    right = int(changes[0]) if len(changes) else forward
    return {
        "source_span": [source_start - left, sa + right],
        "target_span": [target_start - left, ta + right],
        "matching_coordinates": left + anchor_count + right,
        "extension_limit_each_side": maximum,
        "backward_stopped_at_mismatch": left < backward,
        "forward_stopped_at_mismatch": right < forward,
    }
