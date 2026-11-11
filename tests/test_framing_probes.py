import importlib.util
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location(
    "framing_probes", Path(__file__).parents[1] / "scripts" / "framing_probes.py"
)
framing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(framing)


def test_staggered_mapping_has_independent_holdout():
    rng = np.random.default_rng(41)
    b = rng.integers(0, 4, 1200, dtype=np.uint8)
    # Independent construction: A high[n] = NOT B low[n-1]; A low[n] = B high[n+1].
    a = np.zeros_like(b)
    a[1:-1] = (((b[:-2] & 1) ^ 1) << 1) | (b[2:] >> 1)
    result = framing.coordinate_mapping_probe(a, b, train_start=100, holdout_start=700, size=256)
    assert result["mapping"] == {
        "swap_coordinates": True,
        "high_lag": -1,
        "low_lag": 1,
        "xor_mask_high_low": 2,
    }
    assert result["tied_best_candidates"] == 1
    assert result["holdout_matching_symbols"] == 256
    assert result["mapped_changed_symbols"] == 0
    # Training remains exact while a separately corrupted holdout must fail.
    a[750] ^= 1
    result = framing.coordinate_mapping_probe(a, b, train_start=100, holdout_start=700, size=256)
    assert result["training_matching_symbols"] == 256
    assert result["holdout_matching_symbols"] == 255
    assert result["mapped_last_change"] == 750


def test_unrelated_coordinates_do_not_pass_mapping_holdout():
    rng = np.random.default_rng(42)
    a, b = [rng.integers(0, 4, 1200, dtype=np.uint8) for _ in range(2)]
    result = framing.coordinate_mapping_probe(a, b, train_start=100, holdout_start=700, size=256)
    assert result["training_matching_symbols"] < 256
    assert result["holdout_matching_symbols"] < 256


def test_change_summary_keeps_unequal_endpoints():
    a = np.array([0, 1, 2, 3, 1], dtype=np.uint8)
    b = np.array([0, 2, 2, 3], dtype=np.uint8)
    assert framing.change_summary(a, b) == {
        "shared_symbols": 4,
        "lengths": [5, 4],
        "changed_symbols": 1,
        "first_change": 1,
        "last_change": 1,
        "unchanged_suffix_symbols": 2,
    }
