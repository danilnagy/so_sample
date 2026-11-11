"""Verify local endpoint edits without generalizing unresolved trim rules."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.formats.packets import (
    END_TAG,
    START_TAG,
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    replace_calibrated_reference_end,
    sound_data,
)
from po33_re.formats.samples import decode_signed_mulaw, extract_calibrated_window_sound
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_nonzero_trim_minimum import comparison_checks
from scripts.validate_nonzero_trim_recapture import comparison_checks as hardware_checks


def window_frame(
    start=31393,
    end=31504,
    owner_id=0,
    owner_start=0,
    owner_self=0,
    owner_size=65536,
    extra_reference=False,
):
    codes = (np.arange(owner_size) % 255).astype(np.uint8).tobytes()
    owner = (
        owner_start.to_bytes(4, "little")
        + owner_size.to_bytes(4, "little")
        + bytes([owner_self])
        + codes
    )
    reference = start.to_bytes(4, "little") + end.to_bytes(4, "little") + bytes([owner_id])
    packets = [Packet(START_TAG, b""), Packet(0x1234, b"opaque"), Packet(0x68B5, b"\x00")]
    packets.extend(Packet(0xEF78, owner[i : i + 255]) for i in range(0, len(owner), 255))
    packets.extend([Packet(0x68B5, b"\x02"), Packet(0xEF78, reference)])
    if extra_reference:
        packets.append(Packet(0xEF78, b"\x00"))
    packets.append(Packet(END_TAG, b""))
    return decode_frame(encode_packets(packets), start=0)


@pytest.mark.parametrize("endpoint", [31504, 39393, 65535])
def test_fixed_start_endpoint_edit_preserves_unknown_packets_and_all_sample_codes(endpoint):
    frame = window_frame()
    original = frame.encoded_body
    packets = replace_calibrated_reference_end(frame, 3, endpoint)
    edited = decode_frame(encode_packets(packets), start=0)
    assert (
        sound_data(edited, 2)
        == bytes.fromhex("a17a0000") + endpoint.to_bytes(4, "little") + b"\x00"
    )
    assert sound_data(edited, 0) == sound_data(frame, 0)
    assert edited.packets[1] == Packet(0x1234, b"opaque")
    assert encode_packets(replace_calibrated_reference_end(edited, 3, 31504)) == original
    assert frame.encoded_body == original
    assert [i for i, (a, b) in enumerate(zip(frame.packets, packets)) if a != b] == (
        [] if endpoint == 31504 else [len(packets) - 2]
    )


@pytest.mark.parametrize("endpoint", [8000, 31503, 65536, True])
def test_endpoint_writer_rejects_relative_lengths_outside_range_and_boolean_values(endpoint):
    with pytest.raises(ValueError):
        replace_calibrated_reference_end(window_frame(), 3, endpoint)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start": 31392},
        {"end": 31503},
        {"owner_id": 1},
        {"owner_start": 1},
        {"owner_self": 1},
        {"owner_size": 65535},
        {"extra_reference": True},
    ],
)
def test_writer_and_preview_reject_other_starts_and_unknown_ownership_or_layouts(kwargs):
    frame = window_frame(**kwargs)
    unchanged = frame.encoded_body
    with pytest.raises(ValueError):
        replace_calibrated_reference_end(frame, 3, 39393)
    with pytest.raises(ValueError):
        extract_calibrated_window_sound(frame, 3)
    assert frame.encoded_body == unchanged


@pytest.mark.parametrize("slot", [2, 3.0, True])
def test_only_calibrated_sound_slot_is_supported(slot):
    with pytest.raises(ValueError):
        replace_calibrated_reference_end(window_frame(), slot, 39393)


def test_window_preview_uses_explicit_unscaled_half_open_sample_slice():
    frame = window_frame(end=39393)
    preview, report = extract_calibrated_window_sound(frame, 3)
    raw = np.frombuffer(sound_data(frame, 0)[9:], dtype=np.uint8)
    assert np.array_equal(preview, decode_signed_mulaw(raw[31393:39393]))
    assert len(preview) == report["preview_code_count"] == 8000
    assert "inclusivity unresolved" in report["preview_selection_policy"]


@pytest.fixture(scope="module")
def genuine_minimum():
    root = Path(__file__).resolve().parents[1]
    base_path = (
        root / "experiments/event-012-b-sound3-start/derived/analysis-001/capture.symbols.npz"
    )
    capture = root / "experiments/event-013-b-sound3-start-min/capture.wav"
    if not base_path.exists() or not capture.exists():
        pytest.skip("Genuine nonzero-start and minimum recordings required")
    assert (
        sha256_file(capture) == "8c13edb2051ecaf7253b491449826ead3f9083a64c6f4b287cdcb3225dc0682b"
    )
    base, actual = (
        decode_artifact(load_artifact(base_path)),
        decode_artifact(decode_wav(capture, 0.0063)),
    )
    assert (
        hashlib.sha256(actual.encoded_body).hexdigest()
        == "002346273de5b027d53b593e8183b3695ba680bcd01543286def0bc68d24f696"
    )
    registration = json.loads(
        (root / "experiments/sound3-start-min-predictions-001.json").read_text()
    )
    return base, actual, registration


@pytest.mark.capture
def test_genuine_minimum_preserves_start_and_retains_failed_exact_predictions(genuine_minimum):
    checks, hypotheses, packets, changes, values = comparison_checks(*genuine_minimum)
    assert all(checks.values()) and packets == [375]
    assert hypotheses == {"second_field_is_length": False, "second_field_is_endpoint": False}
    assert [c["offset"] for c in changes] == [4, 5]
    assert values["after"] == {"first_u32le": 31393, "second_u32le": 31504, "owner_id": 0}


@pytest.mark.capture
def test_endpoint_writer_reproduces_both_whole_genuine_bodies_and_inverse(genuine_minimum):
    base, actual, _ = genuine_minimum
    assert encode_packets(replace_calibrated_reference_end(actual, 3, 65535)) == base.encoded_body
    assert encode_packets(replace_calibrated_reference_end(base, 3, 31504)) == actual.encoded_body


@pytest.mark.capture
def test_changed_start_is_rejected_even_when_target_packets_have_valid_checksums(genuine_minimum):
    base, actual, registration = genuine_minimum
    packets = list(actual.packets)
    payload = bytearray(packets[375].payload)
    payload[0] ^= 1
    packets[375] = Packet(0xEF78, bytes(payload))
    changed = decode_frame(bytes(4095) + encode_packets(packets))
    checks, _, _, _, _ = comparison_checks(base, changed, registration)
    assert checks["all_packet_checksums"] and not checks["first_field_unchanged"]
    assert not checks["only_allowed_reference_bytes_changed"]


@pytest.mark.capture
def test_endpoint_cli_preserves_inputs_and_produces_the_reviewed_candidate(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = (
        root / "experiments/event-013-b-sound3-start-min/derived/analysis-001/capture.symbols.npz"
    )
    if not source.exists():
        pytest.skip("Reviewed minimum artifact required")
    unchanged = source.read_bytes()
    output, report = tmp_path / "edited.npz", tmp_path / "edit.json"
    args = [
        "set-sound-end",
        str(source),
        "--sound",
        "3",
        "--end",
        "39393",
        "--out",
        str(output),
        "--report",
        str(report),
    ]
    assert main(args) == 0
    result = json.loads(report.read_text())
    assert result["hardware_verified"] is False
    assert (
        result["native_frame"]["encoded_body_sha256"]
        == "b3296f2ed7b3a74cedc79b8d89900e5128c7da1da0e2fed9839d1858412eddfe"
    )
    assert main(args) == 2
    assert main(args[: args.index("--out")] + ["--out", str(source), "--force"]) == 2
    assert source.read_bytes() == unchanged


@pytest.mark.capture
def test_genuine_window_recapture_exact_target_and_valid_checksum_wrong_endpoint_rejection():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-nonzero-trim-001"
    paths = [
        root / "experiments/event-013-b-sound3-start-min/derived/analysis-001/capture.symbols.npz",
        root / "experiments/generated-nonzero-trim-001/edited.symbols.npz",
        directory / "capture.wav",
        directory / "restore-registration.json",
    ]
    if not all(p.exists() for p in paths):
        pytest.skip("Genuine window recapture, source, target and registration required")
    assert (
        sha256_file(paths[2]) == "7935f7cfe3ab7a8b8d45dbe942f3144dad2c7eebb09c8aa52fb06f96a1d632d8"
    )
    original, target = [decode_artifact(load_artifact(p)) for p in paths[:2]]
    actual = decode_artifact(decode_wav(paths[2], 0.0063))
    registration = json.loads(paths[3].read_text())
    checks, packets, changes, values = hardware_checks(original, target, actual, registration)
    assert all(checks.values()) and packets == [375] and len(changes) == 2
    assert values["after"] == {"first_u32le": 31393, "second_u32le": 39393, "owner_id": 0}
    wrong = decode_frame(
        bytes(4095) + encode_packets(replace_calibrated_reference_end(actual, 3, 39394))
    )
    checks, _, _, _ = hardware_checks(original, target, wrong, registration)
    assert checks["all_packet_checksums"] and not checks["registered_body_hash_matches"]
    assert not checks["endpoint_field_matches"]
