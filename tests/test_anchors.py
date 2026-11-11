import numpy as np
import pytest

from po33_re.analysis.anchors import extend_anchor, find_anchor, packed_offsets


def test_anchor_search_checks_every_bit_offset_and_duplicate_hits():
    rng = np.random.default_rng(91)
    needle = rng.integers(0, 2, 64, dtype=np.uint8)
    target = rng.integers(0, 2, 1000, dtype=np.uint8)
    target[101:165] = needle
    target[703:767] = needle
    assert find_anchor(needle, packed_offsets(target), len(target)) == {
        "positions": [101, 703],
        "more_than_limit": False,
    }


def test_search_does_not_match_artificial_zero_padding():
    target = np.array([1] * 10 + [0] * 6, dtype=np.uint8)
    needle = np.zeros(8, dtype=np.uint8)
    assert find_anchor(needle, packed_offsets(target), len(target))["positions"] == []
    assert find_anchor(needle, packed_offsets(np.zeros(100, dtype=np.uint8)), 100, limit=2) == {
        "positions": [0, 1],
        "more_than_limit": True,
    }


def test_anchor_extension_stops_at_known_edges():
    rng = np.random.default_rng(92)
    source = rng.integers(0, 2, 200, dtype=np.uint8)
    target = rng.integers(0, 2, 300, dtype=np.uint8)
    target[113:213] = source[20:120]
    target[112] = source[19] ^ 1
    target[213] = source[120] ^ 1
    result = extend_anchor(source, target, 40, 133, 64)
    assert result["source_span"] == [20, 120]
    assert result["target_span"] == [113, 213]
    assert result["matching_coordinates"] == 100
    assert result["backward_stopped_at_mismatch"] and result["forward_stopped_at_mismatch"]
    with pytest.raises(ValueError):
        extend_anchor(source, target, 40, 133, 64, maximum=-1)
