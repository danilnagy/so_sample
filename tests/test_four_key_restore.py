"""Require genuine whole-frame evidence, including rejection of valid wrong frames."""

import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.clock_decode import decode_clock_wav
from po33_re.modem.symbols import load_artifact
from scripts.validate_four_key_recapture import comparison_checks


@pytest.fixture(scope="module")
def genuine_frames():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-four-keys-001"
    paths = [
        root / "experiments/event-010-b-melodic-key7/derived/analysis-001/capture.symbols.npz",
        root / "experiments/generated-four-keys-001/edited.symbols.npz",
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
        directory / "restore-registration.json",
    ]
    if not all(p.exists() for p in paths):
        pytest.skip("Genuine four-key recapture, acquisition, target and registration required")
    assert (
        sha256_file(paths[2]) == "2cc8b8df219f49e9a0721d67ecf719c37575f9f9da7f264eac5b2c4736eb84bf"
    )
    acquisition = load_artifact(paths[3])
    unchanged = acquisition.to_bytes()
    with pytest.raises(ValueError, match="wire byte9941"):
        decode_artifact(acquisition)
    recovered, report = decode_clock_wav(paths[2], acquisition)
    assert acquisition.to_bytes() == unchanged
    assert report["target_data_used"] is False
    actual = decode_artifact(recovered)
    assert hashlib.sha256(actual.encoded_body).hexdigest() == (
        "9b87309f572b188cd1e1a2651b1ca4feec5cfa8fb669068631042ca8f49465f0"
    )
    original, target = [decode_artifact(load_artifact(p)) for p in paths[:2]]
    registration = json.loads(paths[4].read_text())
    return original, target, actual, registration


@pytest.mark.capture
def test_genuine_four_key_recapture_matches_complete_registered_target(genuine_frames):
    checks, packets, changes, keys = comparison_checks(*genuine_frames)
    assert all(checks.values())
    assert packets == [7]
    assert changes == [
        {"offset": 834, "old": 246, "new": 241},
        {"offset": 898, "old": 240, "new": 246},
        {"offset": 962, "old": 241, "new": 255},
    ]
    assert keys == {"1": 1, "5": 2, "9": 7, "13": 16}


@pytest.mark.capture
def test_original_backup_is_rejected_despite_valid_checksums(genuine_frames):
    original, target, _, registration = genuine_frames
    checks, _, _, _ = comparison_checks(original, target, original, registration)
    assert checks["all_packet_checksums_valid"]
    assert not checks["registered_body_hash_matches"]
    assert not checks["expected_keyboard_keys"]
    assert not all(checks.values())


@pytest.mark.capture
@pytest.mark.parametrize("damage", ["sample", "note"])
def test_checksums_and_matching_steps_do_not_hide_unexpected_edits(genuine_frames, damage):
    original, target, actual, registration = genuine_frames
    packets = list(actual.packets)
    if damage == "sample":
        index = next(
            i
            for i, packet in enumerate(packets)
            if packet.tag == 0xEF78 and len(packet.payload) > 9
        )
        offset = 20
    else:
        index, offset = 7, 834 - 3 * 255
    data = bytearray(packets[index].payload)
    data[offset] ^= 1
    packets[index] = Packet(packets[index].tag, bytes(data))
    changed = decode_frame(encode_packets(packets), start=0)
    checks, _, _, _ = comparison_checks(original, target, changed, registration)
    assert checks["all_packet_checksums_valid"]
    assert checks["expected_populated_steps"]
    assert not checks["registered_body_hash_matches"]
    assert not checks["target_plain_packets_match"]
    assert not checks[
        "sample_packets_unchanged" if damage == "sample" else "expected_keyboard_keys"
    ]
    assert not all(checks.values())
