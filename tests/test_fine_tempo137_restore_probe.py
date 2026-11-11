"""Validate an unobserved fine-tempo target without claiming hardware acceptance."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.globals import set_calibrated_tempo_preset
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_fine_tempo137_restore import restore_checks
from scripts.make_fine_tempo137_restore import fine137_candidate_packets


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-fine-tempo137-001"
    if not (folder / "restore-registration.json").exists():
        pytest.skip("Registered generated fine137 candidate required")
    reg = json.loads((folder / "restore-registration.json").read_text())
    path = root / reg["baseline_artifact"]
    assert sha256_file(path) == reg["baseline_artifact_sha256"]
    assert sha256_file(root / reg["baseline_capture"]) == reg["baseline_capture_sha256"]
    source = decode_artifact(load_artifact(path))
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    return root, folder, source, target, reg


@pytest.mark.capture
def test_saved_fine137_wav_decodes_to_complete_registered_target_while_remaining_unverified(states):
    _, folder, base, target, reg = states
    assert encode_packets(fine137_candidate_packets(base)) == target.encoded_body
    actual = decode_artifact(decode_wav(folder / "restore.wav", 0.02))
    controls, fits, exact, _ = restore_checks(base, target, actual, reg, 137)
    assert all(controls.values()) and all(fits.values()) and all(exact.values())
    report = json.loads((folder / "software-validation.json").read_text())
    assert report["passed"] and not report["hardware_verified"]
    assert report["checks"]["reproduces_entire_genuine60_body"]
    assert report["checks"]["reproduces_entire_genuine240_body"]


@pytest.mark.capture
def test_stale100_has_valid_integrity_but_does_not_match_generated137(states):
    _, _, base, target, reg = states
    controls, fits, exact, _ = restore_checks(base, target, base, reg, 100)
    assert all(controls.values()) and not fits["native_body_changed"]
    assert not exact["entire_recapture_native_body_matches_supplied_target"]
    assert not exact["displayed_BPM_independently_matches137"]


@pytest.mark.capture
def test_missing_display_reading_is_not_inferred_from137_bytes(states):
    _, _, base, target, reg = states
    controls, _, exact, observed = restore_checks(base, target, target, reg)
    assert all(controls.values()) and exact["entire_recapture_native_body_matches_supplied_target"]
    assert exact["displayed_BPM_independently_matches137"] is None
    assert observed["display_after_bpm"] is None


@pytest.mark.capture
def test_wrong_display_remains_inconsistent_even_with_complete_target_bytes(states):
    _, _, base, target, reg = states
    _, fits, exact, _ = restore_checks(base, target, target, reg, 140)
    assert exact["entire_recapture_native_body_matches_supplied_target"]
    assert not fits["candidate_matches_observed_after_BPM"]
    assert not exact["displayed_BPM_independently_matches137"]


@pytest.mark.capture
def test_extra_global_change_is_rejected_even_with_correct137_byte_and_checksums(states):
    _, _, base, target, reg = states
    packets = list(target.packets)
    data = bytearray(packets[2].payload)
    data[130] ^= 1
    packets[2] = Packet(0x7D5C, bytes(data))
    controls, fits, exact, _ = restore_checks(base, target, native(packets), reg, 137)
    assert all(controls.values()) and fits["candidate_matches_observed_after_BPM"]
    assert not fits["only_registered_candidate_byte_changed"]
    assert not exact["entire_recapture_native_body_matches_supplied_target"]


@pytest.mark.capture
def test_research_source_guard_and_public_preset_boundary_are_retained(states):
    _, _, base, target, _ = states
    with pytest.raises(ValueError, match="fine100 native state"):
        fine137_candidate_packets(target)
    with pytest.raises(ValueError, match="Tempo preset"):
        set_calibrated_tempo_preset(base, 137)
