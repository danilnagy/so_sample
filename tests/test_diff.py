import pytest

from po33_re.analysis.diff import compare_bytes


def test_known_diff():
    result = compare_bytes(bytes.fromhex("00 01 02 FF"), bytes.fromhex("00 03 02 FE 99"))
    assert result == {
        "length_a": 4,
        "length_b": 5,
        "overlap_bytes": 4,
        "changed_overlap_bytes": 2,
        "changed_overlap_bits": 2,
        "changed_overlap_percent": 50.0,
        "tail_bytes": 1,
        "changed_ranges": [[1, 2], [3, 4]],
        "identical": False,
    }


@pytest.mark.parametrize(
    "a,b,identical,tail,ranges,bits",
    [
        (b"", b"", True, 0, [], 0),
        (b"", b"abc", False, 3, [], 0),
        (b"abc", b"", False, 3, [], 0),
        (b"abc", b"abc", True, 0, [], 0),
        (b"abc", b"abcd", False, 1, [], 0),
        (b"\x00\x00\x00", b"\xff\xff\xff", False, 0, [[0, 3]], 24),
        (b"\x00\x00\x00", b"\x01\x00\x01", False, 0, [[0, 1], [2, 3]], 2),
    ],
)
def test_edges(a, b, identical, tail, ranges, bits):
    result = compare_bytes(a, b)
    assert result["identical"] is identical
    assert result["tail_bytes"] == tail
    assert result["changed_ranges"] == ranges
    assert result["changed_overlap_bits"] == bits
    if not a or not b:
        assert result["changed_overlap_percent"] is None
