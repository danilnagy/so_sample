"""Constant-plaintext probe for a related-device CRC/additive whitening hypothesis.

Lead: ericlewis/libpo32, MIT, commit3b3a0a758ba452fc809027c5bafcc5e2d0931532.
This independently expressed CRC-CCITT/addition model is not a PO-33 decoder.
"""

import binascii

import numpy as np

from ..modem.symbols import validate_symbols
from .serialization import packed_view

REVERSED_BYTE_BITS = np.packbits(
    np.unpackbits(np.arange(256, dtype=np.uint8)[:, None], axis=1)[:, ::-1], axis=1
).ravel()


def stereo_candidate_bytes(
    left, right, left_mapping, right_mapping, offset, layout, right_first=False
):
    validate_symbols(left)
    validate_symbols(right)
    if sorted(left_mapping) != [0, 1, 2, 3] or sorted(right_mapping) != [0, 1, 2, 3]:
        raise ValueError("Separate channel mappings must be permutations of0..3")
    if layout not in ("stereo_symbols", "stereo_bytes"):
        raise ValueError("Stereo layout required")
    pair = [
        np.array(mapping, dtype=np.uint8)[s]
        for s, mapping in ((left, left_mapping), (right, right_mapping))
    ]
    if right_first:
        pair.reverse()
    return packed_view(*pair, (0, 1, 2, 3), offset, layout)


def constant_codebook(raw):
    if type(raw) is not int or not 0 <= raw <= 255:
        raise ValueError("Constant byte must be0..255")
    initial = np.arange(65536, dtype=np.uint32)
    state = initial.copy()
    key = np.zeros(65536, dtype=np.uint32)
    for byte in range(3):
        coded = (raw + (state & 255)) & 255
        key |= coded << (8 * byte)
        state ^= raw << 8
        for _ in range(8):
            feedback = np.where(state & 32768, 0x1021, 0).astype(np.uint32)
            state = ((state << 1) ^ feedback) & 65535
    order = np.argsort(key, kind="stable")
    return key[order], initial[order]


def constant_plaintext_runs(data, raw, book=None, minimum=16, limit=8):
    if not isinstance(data, np.ndarray) or data.dtype != np.uint8 or data.ndim != 1:
        raise ValueError("Expected one-dimensional uint8 coded bytes")
    if type(minimum) is not int or minimum < 4 or type(limit) is not int or limit <= 0:
        raise ValueError("Minimum>=4 and positive report limit required")
    if len(data) < minimum:
        return {"three_byte_candidates": 0, "validated_runs": 0, "runs": []}
    keys, states = constant_codebook(raw) if book is None else book
    wide = data.astype(np.uint32)
    observed = wide[:-2] | wide[1:-1] << 8 | wide[2:] << 16
    first = np.searchsorted(keys, observed, side="left")
    last = np.searchsorted(keys, observed, side="right")
    candidates = np.flatnonzero((last > first) & (np.arange(len(observed)) + minimum <= len(data)))
    count, validated, runs = 0, 0, []
    raw_byte = bytes([raw])
    for begin in candidates:
        for state_index in range(int(first[begin]), int(last[begin])):
            count += 1
            initial = int(states[state_index])
            state, end = initial, int(begin)
            while end < len(data) and int(data[end]) == (raw + (state & 255)) % 256:
                state = binascii.crc_hqx(raw_byte, state)
                end += 1
            if end - begin >= minimum and len(np.unique(data[begin:end])) > 1:
                validated += 1
                if len(runs) < limit:
                    runs.append(
                        {
                            "byte_span": [int(begin), end],
                            "initial_state": initial,
                            "constant_raw_byte": raw,
                        }
                    )
    return {
        "three_byte_candidates": count,
        "validated_runs": validated,
        "runs": runs,
        "more_runs_than_report_limit": validated > limit,
    }
