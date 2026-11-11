"""Check the imported copy against hardware and distinguish deletion alternatives."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
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
from scripts.check_shared_sound6_deletion import comparison_checks
from scripts.prepare_imported_shared_deletion import FULL_TRANSFER_CHECKS, predict_imported_transfer


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-imported-sound6-to7-copy-001"
    if not (folder / "hardware-acceptance-001.json").exists():
        pytest.skip("Genuine imported copy required")
    acceptance = json.loads((folder / "hardware-acceptance-001.json").read_text())
    assert sha256_file(folder / "capture.wav") == acceptance["capture_sha256"]
    source_path = root / acceptance["artifact_path"]
    assert sha256_file(source_path) == acceptance["artifact_sha256"]
    assert acceptance["hardware_verified"] and all(acceptance["checks"].values())
    actual = decode_artifact(load_artifact(source_path))
    reg = json.loads(
        (
            root
            / "experiments/event-028-b-delete-imported-shared-sound6/deletion-registration.json"
        ).read_text()
    )
    return root, actual, reg


@pytest.mark.capture
def test_copy_plan_compiler_exactly_replays_new_hardware_accepted_wav(states, tmp_path):
    root = states[0]
    source_path = (
        root
        / "experiments/edited-sound6-mono-WAV-import-001/derived/analysis-002/capture.symbols.npz"
    )
    plan_path = root / "experiments/replay-imported-sound6-to7-copy-001/plan.json"
    output = tmp_path / "compiled"
    before = source_path.read_bytes()
    args = ["apply-edits", str(source_path), "--plan", str(plan_path), "--out-dir", str(output)]
    assert main(args) == 0
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments/edited-imported-sound6-to7-copy-001/restore.wav"
    ).read_bytes()
    assert not json.loads((output / "compile-report.json").read_text())["hardware_verified"]
    assert source_path.read_bytes() == before and main(args) == 2


@pytest.mark.capture
def test_registered_transfer_model_passes_and_stale_copy_fails(states):
    _, actual, reg = states
    predicted = native(predict_imported_transfer(actual))
    controls, fits, changed, _, _ = comparison_checks(actual, predicted, reg)
    assert all(controls.values()) and all(fits[name] for name in FULL_TRANSFER_CHECKS)
    assert changed == [5, 6]
    controls, fits, _, _, _ = comparison_checks(actual, actual, reg)
    assert not controls["state_changed_from_baseline"]
    assert not fits["full_transfer_entire_body_matches"]


@pytest.mark.capture
def test_cleared_owner_with_dangling_reference_does_not_pass_transfer(states):
    _, actual, reg = states
    cleared = native(excluding_destination_data(actual, [5]))
    _, fits, _, _, _ = comparison_checks(actual, cleared, reg)
    assert fits["sound6_record_is_empty"] and fits["sound7_reference_still_points_to_old_owner5"]
    assert not fits["sound7_logical_window_preserved"]
    assert not fits["sound7_is_self_owned_full_buffer_with_all_codes_preserved"]


@pytest.mark.capture
def test_tail_code_loss_is_rejected_even_when_used_window_is_preserved(states):
    _, actual, reg = states
    packets = list(predict_imported_transfer(actual))
    transferred = native(packets)
    index = sound_groups(transferred)[6][-1]
    raw = bytearray(packets[index].payload)
    raw[-1] ^= 1
    packets[index] = Packet(0xEF78, bytes(raw))
    controls, fits, _, _, _ = comparison_checks(actual, native(packets), reg)
    assert all(controls.values()) and fits["sound7_logical_window_preserved"]
    assert not fits["sound7_is_self_owned_full_buffer_with_all_codes_preserved"]
    assert not fits["full_transfer_entire_body_matches"]


@pytest.mark.capture
def test_public_shared_deletion_reproduces_genuine_imported_transfer(states):
    root, before, _ = states
    folder = root / "experiments/event-028-b-delete-imported-shared-sound6"
    acceptance = json.loads((folder / "hardware-acceptance-001.json").read_text())
    artifact_path = root / acceptance["artifact_path"]
    assert (
        acceptance["hardware_verified"]
        and sha256_file(artifact_path) == acceptance["artifact_sha256"]
    )
    genuine = decode_artifact(load_artifact(artifact_path))
    assert encode_packets(delete_calibrated_melodic_sound(before, 6)) == genuine.encoded_body


@pytest.mark.capture
def test_last_imported_owner_deletion_reproduces_independent_genuine_empty_state(states):
    transferred = native(delete_calibrated_melodic_sound(states[1], 6))
    root = states[0]
    empty = decode_artifact(
        load_artifact(
            root
            / "experiments/event-029-b-delete-imported-unshared-sound7/derived/analysis-001/capture.symbols.npz"
        )
    )
    assert encode_packets(delete_calibrated_melodic_sound(transferred, 7)) == empty.encoded_body
