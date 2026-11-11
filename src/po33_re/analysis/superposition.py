"""Fixed four-state affine hypotheses; no fitting or payload interpretation."""

import numpy as np

from ..modem.symbols import validate_symbols


def predict_joint(empty, first, second, model):
    for values in (empty, first, second):
        validate_symbols(values)
    count = min(len(empty), len(first), len(second))
    if not count:
        raise ValueError("Nonempty shared span required")
    a, b, c = [v[:count] for v in (empty, first, second)]
    if model == "coordinate_xor":
        return a ^ b ^ c
    if model == "add_mod4":
        return ((b.astype(np.int16) + c - a) % 4).astype(np.uint8)
    raise ValueError("Unknown joint-state hypothesis")


def compare_prediction(predicted, actual):
    validate_symbols(predicted)
    validate_symbols(actual)
    count = min(len(predicted), len(actual))
    changed = np.flatnonzero(predicted[:count] != actual[:count])
    return {
        "shared_count": count,
        "prediction_count": len(predicted),
        "actual_count": len(actual),
        "shared_span_matches": not bool(len(changed)),
        "full_counts_and_content_match": not bool(len(changed)) and len(predicted) == len(actual),
        "changed_count": len(changed),
        "first_change": int(changed[0]) if len(changed) else None,
        "last_change": int(changed[-1]) if len(changed) else None,
        "first_changed_indices_limit32": changed[:32].tolist(),
    }
