from pathlib import Path

import pytest

from po33_re.formats.packets import (
    END_TAG,
    START_TAG,
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
)
from po33_re.formats.patterns import clone_step, pattern_data, patterns_report
from po33_re.modem.symbols import load_artifact


@pytest.mark.capture
@pytest.mark.parametrize(
    "name,steps,aux",
    [
        ("event-001-b", [1], [16]),
        ("event-002-b", [2], [17]),
        ("event-003-b", [3], [16]),
        ("event-005-b-joint", [1, 2], [16, 16]),
    ],
)
def test_genuine_kick_layout_preserves_event_and_auxiliary_bytes(name, steps, aux):
    root = Path(__file__).resolve().parents[1]
    analysis = "analysis-002" if name == "event-005-b-joint" else "analysis-001"
    path = root / f"experiments/{name}/derived/{analysis}/capture.symbols.npz"
    if not path.exists():
        pytest.skip("Reviewed controlled kick artifact required")
    frame = decode_artifact(load_artifact(path))
    data = pattern_data(frame, 1)
    expected = bytearray(1024) + bytes([255]) * 8
    for step, auxiliary in zip(steps, aux):
        offset = 48 * (step - 1) + 24
        expected[offset : offset + 3] = bytes.fromhex("cf f6 83")
        expected[768 + 16 * (step - 1) + 8] = auxiliary
    assert data == bytes(expected)
    report = patterns_report(frame)["patterns"][0]
    assert [row["step"] for row in report["nonzero_step_rows"]] == steps
    assert report["opaque_footer_hex"] == "ffffffffffffffff"
    assert not report["all_primary_and_auxiliary_bytes_zero"]


def synthetic_pattern_packets():
    packets = [Packet(START_TAG, b"")]
    for pattern in range(16):
        packets.append(Packet(0xA041, bytes([pattern])))
        data = bytes(1024) + bytes([255]) * 8
        packets.extend(Packet(0xC498, data[i : i + 255]) for i in range(0, len(data), 255))
    packets.append(Packet(END_TAG, b""))
    return packets


@pytest.mark.parametrize(
    "damage", ["duplicate", "missing", "out_of_range", "short_data", "unselected_data"]
)
def test_reader_rejects_unobserved_or_malformed_pattern_layout(damage):
    packets = synthetic_pattern_packets()
    if damage == "duplicate":
        packets[7] = Packet(0xA041, b"\x00")
    elif damage == "missing":
        del packets[7:13]
    elif damage == "out_of_range":
        packets[1] = Packet(0xA041, b"\x10")
    elif damage == "short_data":
        packets[2] = Packet(0xC498, bytes(254))
    else:
        packets.insert(1, Packet(0xC498, b"\x00"))
    frame = decode_frame(encode_packets(packets), start=0)
    with pytest.raises(ValueError):
        patterns_report(frame)


def test_empty_raw_rows_and_invalid_slot_are_explicit():
    frame = decode_frame(encode_packets(synthetic_pattern_packets()), start=0)
    report = patterns_report(frame)
    assert len(report["patterns"]) == 16
    assert all(p["all_primary_and_auxiliary_bytes_zero"] for p in report["patterns"])
    assert all(not p["nonzero_step_rows"] for p in report["patterns"])
    with pytest.raises(ValueError):
        pattern_data(frame, 0)


def single_event_frame():
    packets = synthetic_pattern_packets()
    data = bytearray(1024) + bytes([255]) * 8
    data[6:9] = bytes.fromhex("0d f8 83")
    data[770] = 240
    for i, offset in enumerate(range(0, len(data), 255), start=2):
        packets[i] = Packet(0xC498, bytes(data[offset : offset + 255]))
    return decode_frame(encode_packets(packets), start=0)


def test_opaque_step_clone_preserves_source_and_footer_across_chunk_edges():
    frame = single_event_frame()
    before = encode_packets(frame.packets)
    packets = clone_step(frame, 1, 1, [5, 9, 13, 16])
    edited = decode_frame(encode_packets(packets), start=0)
    data = pattern_data(edited, 1)
    expected = bytearray(pattern_data(frame, 1))
    for step in (5, 9, 13, 16):
        expected[48 * (step - 1) + 6 : 48 * (step - 1) + 9] = bytes.fromhex("0d f8 83")
        expected[768 + 16 * (step - 1) + 2] = 240
    assert data == bytes(expected)
    assert encode_packets(frame.packets) == before
    assert len(packets) == len(frame.packets)
    for original, changed in zip(frame.packets, packets):
        assert original.tag == changed.tag and len(original.payload) == len(changed.payload)
    for slot in range(2, 17):
        assert pattern_data(frame, slot) == pattern_data(edited, slot)


@pytest.mark.parametrize(
    "source,targets",
    [(0, [2]), (1, []), (1, [0]), (1, [17]), (1, [True]), (1, [2, 2]), (1, [1]), (2, [3])],
)
def test_clone_rejects_invalid_steps_or_empty_source(source, targets):
    frame = single_event_frame()
    with pytest.raises(ValueError):
        clone_step(frame, 1, source, targets)


def test_clone_rejects_occupied_targets_and_unobserved_source_layout():
    frame = single_event_frame()
    edited = decode_frame(encode_packets(clone_step(frame, 1, 1, [2])), start=0)
    with pytest.raises(ValueError):
        clone_step(edited, 1, 1, [2])
    packets = list(frame.packets)
    # Give the auxiliary row a second occupied cell; do not silently copy it.
    data = bytearray(packets[5].payload)
    data[6] = 240  # Absolute offset771 in the fourth chunk.
    packets[5] = Packet(0xC498, bytes(data))
    malformed = decode_frame(encode_packets(packets), start=0)
    with pytest.raises(ValueError):
        clone_step(malformed, 1, 1, [2])


@pytest.mark.capture
def test_clone_reproduces_genuine_corrected_joint_packet_body():
    root = Path(__file__).resolve().parents[1]
    source = root / "experiments/event-001-b/derived/analysis-001/capture.symbols.npz"
    target = root / "experiments/event-005-b-joint/derived/analysis-002/capture.symbols.npz"
    if not source.exists() or not target.exists():
        pytest.skip("Genuine single kick and corrected joint artifacts required")
    frame, recorded = [decode_artifact(load_artifact(p)) for p in (source, target)]
    assert encode_packets(clone_step(frame, 1, 1, [2])) == recorded.encoded_body


@pytest.mark.capture
def test_genuine_melodic_step1_changes_only_registered_note_bytes():
    import hashlib

    from po33_re.artifacts import sha256_file
    from po33_re.modem.decode import decode_wav

    root = Path(__file__).resolve().parents[1]
    paths = [
        root / f"experiments/{name}/capture.wav"
        for name in ("edited-sample-001", "event-007-b-melodic")
    ]
    if not all(p.exists() for p in paths):
        pytest.skip("Genuine empty baseline and melodic note WAV required")
    assert (
        sha256_file(paths[1]) == "4b5a18904460369f01abd6dce3d621b8264ccc1aee9f5b8d273e3c1db79dcb5f"
    )
    before, after = [decode_artifact(decode_wav(p, 0.0063)) for p in paths]
    assert hashlib.sha256(after.encoded_body).hexdigest() == (
        "c5a4889ed680aa756c0a04f2df92bd194319f79a6de1603a20558976043e67a9"
    )
    a, b = pattern_data(before, 1), pattern_data(after, 1)
    assert [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y] == [
        (6, 0, 13),
        (7, 0, 248),
        (8, 0, 131),
        (770, 0, 240),
    ]
    assert len(before.packets) == len(after.packets) == 511
    assert [i for i, (x, y) in enumerate(zip(before.packets, after.packets)) if x != y] == [4, 7]
