"""Verify independently known empty-state predictions and retain last-owner guards."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.edits import apply_plan
from po33_re.formats.lifecycle import delete_calibrated_melodic_sound
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data
from scripts.check_unshared_sound7_deletion import comparison_checks
from scripts.prepare_imported_unshared_deletion import REMOVAL_CHECKS


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-029-b-delete-imported-unshared-sound7"
    if not (directory / "deletion-registration.json").exists():
        pytest.skip("Registered imported last-owner deletion control required")
    reg = json.loads((directory / "deletion-registration.json").read_text())
    path = root / reg["baseline_artifact"]
    assert sha256_file(path) == reg["baseline_artifact_sha256"]
    assert sha256_file(root / reg["baseline_capture"]) == reg["baseline_source_sha256"]
    before = decode_artifact(load_artifact(path))
    earlier = decode_artifact(
        load_artifact(
            root / reg["empty_record_model"]["independently_observed_matching_state_artifact"]
        )
    )
    target = native(excluding_destination_data(before, [6]))
    return root, before, earlier, target, reg


@pytest.mark.capture
def test_last_owner_removal_prediction_equals_entire_independent_genuine_state(states):
    _, before, earlier, target, reg = states
    controls, fits, observed = comparison_checks(before, target, reg)
    assert all(controls.values()) and all(fits[name] for name in REMOVAL_CHECKS)
    assert target.encoded_body == earlier.encoded_body
    assert observed["changed_selector_ids"] == [6]
    assert len(target.packets) == 815 and target.end_byte == 156758


@pytest.mark.capture
def test_retained_backing_codes_with_changed_metadata_are_distinguished_from_removal(states):
    _, before, _, _, reg = states
    packets = list(before.packets)
    index = sound_groups(before)[6][0]
    raw = packets[index].payload
    packets[index] = Packet(0xEF78, raw[:4] + (17580).to_bytes(4, "little") + raw[8:])
    controls, fits, _ = comparison_checks(before, native(packets), reg)
    assert all(controls.values()) and fits["full_codes_retained_under_owner6"]
    assert not fits["sound7_record_is_empty"] and not fits["entire_empty_record_model_matches"]


@pytest.mark.capture
def test_stale_transferred_state_is_rejected(states):
    _, before, _, _, reg = states
    controls, fits, _ = comparison_checks(before, before, reg)
    assert not controls["state_changed_from_baseline"]
    assert not fits["entire_empty_record_model_matches"]


@pytest.mark.capture
def test_composed_public_imported_copy_and_shared_deletion_match_genuine_transfer(states):
    root, genuine, _, _, _ = states
    path = (
        root
        / "experiments/edited-sound6-mono-WAV-import-001/derived/analysis-002/capture.symbols.npz"
    )
    source = load_artifact(path)
    before = source.to_bytes()
    plan = json.loads(
        (root / "experiments/replay-imported-sound6-to7-copy-001/plan.json").read_text()
    )
    plan["operations"].append({"operation": "delete_melodic_sound", "sound": 6})
    edited, trace = apply_plan(source, sha256_file(path), plan)
    assert decode_artifact(edited).encoded_body == genuine.encoded_body
    assert source.to_bytes() == before and len(trace) == 2
    assert not edited.metadata["hardware_verified"]


@pytest.mark.capture
def test_full_imported_cycle_compiler_replays_independently_accepted_wav(states, tmp_path):
    root = states[0]
    path = (
        root
        / "experiments/edited-sound6-mono-WAV-import-001/derived/analysis-002/capture.symbols.npz"
    )
    plan_path = root / "experiments/replay-imported-melodic-lifecycle-cycle-001/plan.json"
    output = tmp_path / "compiled"
    assert main(["apply-edits", str(path), "--plan", str(plan_path), "--out-dir", str(output)]) == 0
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments/edited-sound4-shrink-001/restore.wav"
    ).read_bytes()
    assert not json.loads((output / "compile-report.json").read_text())["hardware_verified"]


@pytest.mark.capture
def test_last_owner_deletion_still_rejects_unobserved_endpoint(states):
    before = states[1]
    packets = list(before.packets)
    index = sound_groups(before)[6][0]
    raw = packets[index].payload
    packets[index] = Packet(0xEF78, raw[:4] + (17580).to_bytes(4, "little") + raw[8:])
    with pytest.raises(ValueError, match="deletion layout"):
        delete_calibrated_melodic_sound(native(packets), 7)
