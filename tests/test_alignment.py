import numpy as np
import pytest

from po33_re.analysis.alignment import equality_runs


def test_displaced_run_has_exact_source_and_target_edges():
    rng = np.random.default_rng(97)
    source = rng.integers(0, 4, 1000, dtype=np.uint8)
    target = rng.integers(0, 4, 1000, dtype=np.uint8)
    target[316:716] = source[400:800]
    target[315] = (source[399] + 1) % 4
    target[716] = (source[800] + 1) % 4
    report = equality_runs(source, target, -84, source_start=300)
    run = report["longest_runs"][0]
    assert run["source_span"] == [400, 800] and run["target_span"] == [316, 716]
    assert run["matching_values"] == 400 and run["distinct_values"] == [0, 1, 2, 3]
    assert not report["alignment_applied_to_artifacts"]


def test_offset_bounds_and_no_equal_runs():
    source = np.zeros(100, dtype=np.uint8)
    target = np.ones(100, dtype=np.uint8)
    report = equality_runs(source, target, 20)
    assert report["source_comparison_span"] == [0, 80]
    assert report["target_comparison_span"] == [20, 100]
    assert report["longest_runs"] == [] and report["equal_fraction"] == 0
    with pytest.raises(ValueError):
        equality_runs(source, target, 100)
