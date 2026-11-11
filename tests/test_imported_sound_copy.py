"""Bind actual mono import evidence and reject unsafe copies of its backing owner."""

import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.lifecycle import copy_calibrated_melodic_reference
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.formats.samples import encode_signed_mulaw
from po33_re.modem.symbols import load_artifact
from po33_re.sample_import import import_sound6_packets, prepare_pcm_sample
from scripts.check_mono_WAV_import_restore import comparison_checks as import_checks
from scripts.check_sound6_to7_copy_restore import comparison_checks as copy_checks
from scripts.make_imported_sound6_to7_copy import copy_imported_reference


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-sound6-mono-WAV-import-001"
    acceptance_path = folder / "hardware-acceptance-001.json"
    if not acceptance_path.exists():
        pytest.skip("Actual accepted mono import required")
    acceptance = json.loads(acceptance_path.read_text())
    source_path = root / acceptance["artifact_path"]
    assert acceptance["hardware_verified"] and all(acceptance["checks"].values())
    assert sha256_file(source_path) == acceptance["artifact_sha256"]
    assert sha256_file(folder / "capture.wav") == acceptance["capture_sha256"]
    actual = decode_artifact(load_artifact(source_path))
    baseline = decode_artifact(
        load_artifact(
            root / json.loads((folder / "restore-registration.json").read_text())["source_artifact"]
        )
    )
    sample, _ = prepare_pcm_sample((folder / "input-sample.wav").read_bytes())
    return root, folder, baseline, actual, sample


@pytest.mark.capture
def test_actual_mono_recapture_reproduces_saved_pcm_import_without_using_target_for_decoding(
    states,
):
    _, folder, before, actual, sample = states
    target = native(import_sound6_packets(before, 6, sample)[0])
    registration = json.loads((folder / "restore-registration.json").read_text())
    checks, fits, _ = import_checks(before, target, actual, registration)
    assert all(checks.values()) and all(fits.values())
    assert (
        hashlib.sha256(actual.encoded_body).hexdigest()
        == "5b557a2586907b90705bed847b63e33745d0cef85bc27e06f80e6f0601f29b7c"
    )


@pytest.mark.capture
def test_copy_probe_changes_only_one_reference_and_checker_rejects_stale_state(states):
    root, _, _, actual, _ = states
    target = native(copy_imported_reference(actual))
    registration = json.loads(
        (
            root / "experiments/edited-imported-sound6-to7-copy-001/restore-registration.json"
        ).read_text()
    )
    assert all(copy_checks(actual, target, target, registration).values())
    assert not all(copy_checks(actual, target, actual, registration).values())
    assert len(target.packets) == len(actual.packets) + 1
    assert len(target.encoded_body) == len(actual.encoded_body) + 14


@pytest.mark.capture
def test_public_copy_reproduces_genuine_imported_copy_body(states):
    root, _, _, actual, _ = states
    folder = root / "experiments/edited-imported-sound6-to7-copy-001"
    acceptance = json.loads((folder / "hardware-acceptance-001.json").read_text())
    path = root / acceptance["artifact_path"]
    assert sha256_file(path) == acceptance["artifact_sha256"]
    genuine = decode_artifact(load_artifact(path))
    assert encode_packets(copy_calibrated_melodic_reference(actual, 6, 7)) == genuine.encoded_body


@pytest.mark.capture
def test_public_copy_still_rejects_unobserved_endpoint(states):
    _, _, _, actual, _ = states
    packets = list(actual.packets)
    index = sound_groups(actual)[5][0]
    data = packets[index].payload
    packets[index] = Packet(0xEF78, data[:4] + (17580).to_bytes(4, "little") + data[8:])
    with pytest.raises(ValueError, match="source layout"):
        copy_calibrated_melodic_reference(native(packets), 6, 7)


@pytest.mark.capture
def test_import_rejects_copy_probe_shared_owner(states):
    _, _, _, actual, sample = states
    copied = native(copy_imported_reference(actual))
    with pytest.raises(ValueError, match="referrers"):
        import_sound6_packets(copied, 6, sample)
    with pytest.raises(ValueError, match="empty Sound7"):
        copy_imported_reference(copied)


@pytest.mark.capture
def test_probe_rejects_owner_payload_corruption_with_recomputed_checksums(states):
    _, _, _, actual, _ = states
    packets = list(actual.packets)
    index = sound_groups(actual)[5][1]
    data = bytearray(packets[index].payload)
    data[19] ^= 1
    packets[index] = Packet(0xEF78, bytes(data))
    with pytest.raises(ValueError, match="verified imported chirp"):
        copy_imported_reference(native(packets))


@pytest.mark.capture
def test_wrong_reference_endpoint_with_valid_checksums_is_rejected(states):
    root, _, _, actual, _ = states
    packets = list(copy_imported_reference(actual))
    target = native(packets)
    index = sound_groups(target)[6][0]
    packets[index] = Packet(0xEF78, bytes(4) + (17580).to_bytes(4, "little") + b"\x05")
    wrong = native(packets)
    registration = json.loads(
        (
            root / "experiments/edited-imported-sound6-to7-copy-001/restore-registration.json"
        ).read_text()
    )
    checks = copy_checks(actual, target, wrong, registration)
    assert checks["all_native_checksums"] and checks["sound6_full_buffer_preserved"]
    assert not checks["sound7_exact_reference"]
    assert not checks["entire_recaptured_native_body_matches_target"]


@pytest.mark.capture
def test_reimporting_accepted_mono_window_preserves_body_exactly(states):
    _, _, _, actual, sample = states
    assert encode_packets(import_sound6_packets(actual, 6, sample)[0]) == actual.encoded_body
    assert len(encode_signed_mulaw(sample)) == 17579
