import numpy as np
import pytest

from po33_re.analysis.staggered import (
    constant_runs,
    phase_increments,
    restore_labels,
    staggered_phases,
)


def test_known_grouping_and_circular_order():
    # Cells: (H1,L0)=10, (H2,L1)=11, (H3,L2)=01, (H4,L3)=00.
    raw = np.array([0, 3, 3, 0, 0], dtype=np.uint8)
    assert staggered_phases(raw).tolist() == [0, 1, 2, 3]
    assert phase_increments(np.array([3, 0, 2, 1], dtype=np.uint8)).tolist() == [1, 2, 3]


def test_lossless_inverse_retains_both_boundary_coordinates():
    rng = np.random.default_rng(71)
    for size in (2, 3, 128, 10000):
        raw = rng.integers(0, 4, size, dtype=np.uint8)
        phases = staggered_phases(raw)
        assert np.array_equal(restore_labels(phases, int(raw[0] >> 1), int(raw[-1] & 1)), raw)
        if size > 2:
            increments = phase_increments(phases)
            recovered = (int(phases[0]) + np.r_[0, np.cumsum(increments)]) % 4
            assert np.array_equal(recovered, phases)


def test_coordinate_mapping_becomes_quarter_turn():
    rng = np.random.default_rng(72)
    b = rng.integers(0, 4, 10000, dtype=np.uint8)
    a = np.zeros_like(b)
    a[1:-1] = (((b[:-2] & 1) ^ 1) << 1) | (b[2:] >> 1)
    pa, pb = staggered_phases(a), staggered_phases(b)
    assert np.all((pa[1:-1].astype(np.int16) - pb[1:-1]) % 4 == 1)
    assert np.array_equal(phase_increments(pa)[1:-1], phase_increments(pb)[1:-1])


def test_constant_runs_report_exact_boundaries():
    values = np.array([0, 0, 0, 1, 2, 2, 2, 2, 3], dtype=np.uint8)
    assert constant_runs(values, minimum=3) == [
        {"span": [0, 3], "phase_offset_mod4": 0},
        {"span": [4, 8], "phase_offset_mod4": 2},
    ]
    assert constant_runs(np.array([], dtype=np.uint8)) == []


def test_invalid_short_and_nonbinary_boundary_inputs():
    with pytest.raises(ValueError):
        staggered_phases(np.array([2], dtype=np.uint8))
    with pytest.raises(ValueError):
        phase_increments(np.array([0], dtype=np.uint8))
    with pytest.raises(ValueError):
        restore_labels(np.array([0], dtype=np.uint8), 2, 0)
