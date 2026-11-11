import copy
import json

import numpy as np
import pytest

from po33_re.modem.symbols import (
    PHASE_CONVENTION,
    SCHEMA,
    SymbolArtifact,
    load_artifact,
    pack_symbols,
    unpack_symbols,
)


def artifact(left=None, right=None):
    left = np.array([3, 2, 0, 1, 2], dtype=np.uint8) if left is None else left
    right = np.array([0, 1], dtype=np.uint8) if right is None else right
    metadata = {
        "schema": SCHEMA,
        "schema_version": 1,
        "phase_convention": PHASE_CONVENTION,
        "source_sha256": "a" * 64,
        "channel_order": ["left", "right"],
        "sample_rate_hz": 44100,
        "decoder_version": "test-independent-vectors",
        "transformations": [],
        "channels": {
            name: {
                "symbol_count": len(values),
                "boundaries": {},
                "discarded_samples": {},
                "uncertainty": {"status": "test"},
            }
            for name, values in (("left", left), ("right", right))
        },
    }
    return SymbolArtifact(left, right, metadata)


def test_hand_calculated_packing():
    values = np.array([3, 2, 0, 1, 2], dtype=np.uint8)
    data, report = pack_symbols(values)
    assert data == bytes.fromhex("4b 02")
    assert report["symbol_count"] == 5
    assert report["padding_symbols"] == 3
    assert np.array_equal(unpack_symbols(bytes.fromhex("4b 02"), 5), values)


@pytest.mark.parametrize("count", range(10))
def test_all_partial_groups(count):
    values = (np.arange(count) % 4).astype(np.uint8)
    data, report = pack_symbols(values)
    assert len(data) == (count + 3) // 4
    assert report["padding_symbols"] == (-count) % 4
    assert np.array_equal(unpack_symbols(data, count), values)


def test_padding_and_count_validation():
    with pytest.raises(ValueError, match="padding"):
        unpack_symbols(b"\xff", 1)
    with pytest.raises(ValueError, match="length"):
        unpack_symbols(b"\x00", 5)
    with pytest.raises(ValueError):
        unpack_symbols(b"", True)
    for invalid in (
        np.array([4], dtype=np.uint8),
        np.array([0], dtype=np.int32),
        np.zeros((1, 1), dtype=np.uint8),
    ):
        with pytest.raises(ValueError):
            pack_symbols(invalid)


def test_npz_deterministic_and_unequal_channels(tmp_path):
    a = artifact()
    first = a.to_bytes()
    assert first == a.to_bytes()
    path = tmp_path / "symbols.npz"
    path.write_bytes(first)
    b = load_artifact(path)
    assert np.array_equal(a.left_symbols, b.left_symbols)
    assert np.array_equal(a.right_symbols, b.right_symbols)
    assert len(b.left_symbols) == 5 and len(b.right_symbols) == 2
    assert b.metadata == a.metadata


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema", "unknown"),
        ("schema_version", 2),
        ("phase_convention", "differential"),
        ("channel_order", ["right", "left"]),
        ("sample_rate_hz", 0),
        ("source_sha256", "bad"),
        ("decoder_version", None),
        ("transformations", None),
    ],
)
def test_invalid_metadata(field, value):
    a = artifact()
    a.metadata[field] = value
    with pytest.raises(ValueError):
        a.to_bytes()


def test_counts_and_pickle_rejected(tmp_path):
    a = artifact()
    a.metadata["channels"]["left"]["symbol_count"] = 4
    with pytest.raises(ValueError, match="count"):
        a.to_bytes()
    path = tmp_path / "bad.npz"
    good = artifact()
    np.savez(
        path,
        left_symbols=np.array([object()], dtype=object),
        right_symbols=good.right_symbols,
        metadata_json=np.array(json.dumps(copy.deepcopy(good.metadata))),
    )
    with pytest.raises(ValueError, match="allow_pickle"):
        load_artifact(path)
    path.write_bytes(b"not an npz")
    with pytest.raises(ValueError):
        load_artifact(path)
