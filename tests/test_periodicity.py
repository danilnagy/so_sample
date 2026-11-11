import numpy as np
import pytest

from po33_re.analysis.periodicity import lag_runs, lag_similarity, smallest_period


def test_fft_similarity_matches_direct_equality_counts():
    rng = np.random.default_rng(93)
    values = rng.integers(0, 4, 500, dtype=np.uint8)
    measured = lag_similarity(values, 100)
    expected = np.array([np.mean(values[:-p] == values[p:]) for p in range(1, 101)])
    assert np.allclose(measured, expected, atol=1e-12)


def test_exact_period_and_run_boundaries():
    values = np.tile(np.array([0, 0, 1, 2, 3, 1, 3], dtype=np.uint8), 100)
    assert smallest_period(values, 50) == 7
    assert lag_similarity(values, 50)[6] == pytest.approx(1)
    assert lag_runs(values, 7, window_start=0, limit=1) == [
        {
            "equal_comparison_span": [0, 693],
            "covered_value_span": [0, 700],
            "matching_lag_pairs": 693,
        }
    ]
    with pytest.raises(ValueError):
        lag_similarity(values, len(values))
