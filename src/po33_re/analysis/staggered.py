"""Reassociate staggered sign coordinates; no claim of decoded protocol symbols."""

from itertools import pairwise

import numpy as np

from ..modem.symbols import validate_symbols

# Circular order under (H,L) -> (NOT L,H): 10 -> 11 -> 01 -> 00.
CIRCULAR_INDEX = np.array([3, 2, 0, 1], dtype=np.uint8)
LABEL_FROM_INDEX = np.array([2, 3, 1, 0], dtype=np.uint8)


def staggered_phases(symbols: np.ndarray) -> np.ndarray:
    """Cell n groups high[n+1] with low[n]; output has N-1 entries."""
    validate_symbols(symbols)
    if len(symbols) < 2:
        raise ValueError("At least two labels required for staggered reassociation")
    cells = (symbols[1:] & 2) | (symbols[:-1] & 1)
    return CIRCULAR_INDEX[cells]


def phase_increments(phases: np.ndarray) -> np.ndarray:
    validate_symbols(phases)
    if len(phases) < 2:
        raise ValueError("At least two phases required for an increment")
    return ((phases[1:].astype(np.int16) - phases[:-1]) % 4).astype(np.uint8)


def restore_labels(phases: np.ndarray, initial_high: int, final_low: int) -> np.ndarray:
    """Inverse grouping with the two explicitly retained boundary coordinates."""
    validate_symbols(phases)
    if not len(phases) or initial_high not in (0, 1) or final_low not in (0, 1):
        raise ValueError("Nonempty phases and binary boundary coordinates required")
    cells = LABEL_FROM_INDEX[phases]
    result = np.empty(len(phases) + 1, dtype=np.uint8)
    result[0] = (initial_high << 1) | (cells[0] & 1)
    result[1:-1] = (cells[:-1] & 2) | (cells[1:] & 1)
    result[-1] = (cells[-1] & 2) | final_low
    return result


def constant_runs(values: np.ndarray, minimum: int = 64) -> list[dict]:
    validate_symbols(values)
    if type(minimum) is not int or minimum <= 0:
        raise ValueError("Minimum run length must be a positive integer")
    if not len(values):
        return []
    boundaries = np.r_[0, np.flatnonzero(values[1:] != values[:-1]) + 1, len(values)]
    return [
        {"span": [int(start), int(end)], "phase_offset_mod4": int(values[start])}
        for start, end in pairwise(boundaries)
        if end - start >= minimum
    ]
