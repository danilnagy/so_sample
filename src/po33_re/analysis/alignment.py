"""Diagnostic equality runs at explicit offsets; never rewrite stored phase arrays."""

import numpy as np

from ..modem.symbols import validate_symbols


def equality_runs(source, target, shift, source_start=0, limit=8):
    validate_symbols(source)
    validate_symbols(target)
    if (
        type(shift) is not int
        or type(source_start) is not int
        or source_start < 0
        or type(limit) is not int
        or limit <= 0
    ):
        raise ValueError("Integer shift, nonnegative start and positive limit required")
    begin = max(source_start, -shift, 0)
    end = min(len(source), len(target) - shift)
    if begin >= end:
        raise ValueError("No shared span at this offset")
    equal = source[begin:end] == target[begin + shift : end + shift]
    edges = np.diff(np.r_[0, equal, 0].astype(np.int8))
    starts = np.flatnonzero(edges == 1) + begin
    ends = np.flatnonzero(edges == -1) + begin
    order = np.argsort(ends - starts)[-limit:][::-1]
    return {
        "shift": shift,
        "source_comparison_span": [begin, end],
        "target_comparison_span": [begin + shift, end + shift],
        "equal_fraction": float(np.mean(equal)),
        "alignment_applied_to_artifacts": False,
        "longest_runs": [
            {
                "source_span": [int(starts[i]), int(ends[i])],
                "target_span": [int(starts[i] + shift), int(ends[i] + shift)],
                "matching_values": int(ends[i] - starts[i]),
                "distinct_values": np.unique(source[starts[i] : ends[i]]).astype(int).tolist(),
            }
            for i in order
        ],
    }
