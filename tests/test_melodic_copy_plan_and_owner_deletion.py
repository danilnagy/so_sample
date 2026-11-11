"""Replay a validated copy plan and distinguish physical last-owner deletion outcomes."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.edits import apply_plan
from po33_re.formats.lifecycle import copy_calibrated_melodic_reference
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_data,
    sound_groups,
)
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data
from scripts.check_shared_sound6_deletion import comparison_checks as shared_checks
from scripts.check_unshared_sound7_deletion import comparison_checks as unshared_checks


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def sources():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/event-026-b-delete-shared-sound6"
    if not (folder / "capture.wav").exists():
        pytest.skip("Physical shared-owner deletion capture required")
    assert (
        sha256_file(folder / "capture.wav")
        == "85944505d73d4a6097800da7220bf34badec35633286e1a2771476b9479c9c7b"
    )
    actual = decode_artifact(decode_wav(folder / "capture.wav", 0.0063))
    shared_reg = json.loads(
        (root / "experiments/shared-sound6-deletion-predictions-001.json").read_text()
    )
    unshared_reg = json.loads(
        (root / "experiments/unshared-sound7-deletion-predictions-001.json").read_text()
    )
    return root, actual, shared_reg, unshared_reg


@pytest.mark.capture
def test_actual_shared_deletion_moves_every_code_and_exactly_matches_preregistered_body(sources):
    root, actual, reg, _ = sources
    base = decode_artifact(load_artifact(root / reg["baseline_artifact"]))
    checks, fits, changed, _, _ = shared_checks(base, actual, reg)
    assert all(checks.values()) and changed == [5, 6]
    assert fits["full_transfer_entire_body_matches"] and fits["sound7_logical_window_preserved"]
    assert not sound_groups(actual)[5]
    assert sound_data(actual, 6)[9:] == sound_data(base, 5)[9:]


@pytest.mark.capture
def test_copy_plan_replays_complete_hardware_accepted_copy_body_without_mutating_source(sources):
    root = sources[0]
    source_path = (
        root / "experiments/edited-sound6-create-001/derived/analysis-001/capture.symbols.npz"
    )
    source = load_artifact(source_path)
    before = source.to_bytes()
    plan = json.loads((root / "experiments/replay-sound6-to7-copy-001/plan.json").read_text())
    edited, trace = apply_plan(source, sha256_file(source_path), plan)
    accepted = decode_artifact(
        load_artifact(
            root / "experiments/edited-sound6-to7-copy-001/derived/analysis-001/capture.symbols.npz"
        )
    )
    assert decode_artifact(edited).encoded_body == accepted.encoded_body
    assert source.to_bytes() == before and not edited.metadata["hardware_verified"]
    assert len(trace) == 1 and trace[0]["operation"]["operation"] == "copy_melodic_reference"


@pytest.mark.capture
def test_copy_plan_compiler_matches_original_hardware_accepted_wav_and_refuses_overwrite(
    sources, tmp_path
):
    root = sources[0]
    source_path = (
        root / "experiments/edited-sound6-create-001/derived/analysis-001/capture.symbols.npz"
    )
    plan_path = root / "experiments/replay-sound6-to7-copy-001/plan.json"
    output = tmp_path / "copy"
    args = ["apply-edits", str(source_path), "--plan", str(plan_path), "--out-dir", str(output)]
    assert main(args) == 0
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments/edited-sound6-to7-copy-001/restore.wav"
    ).read_bytes()
    report = json.loads((output / "compile-report.json").read_text())
    assert report["passed"] and not report["hardware_verified"]
    assert main(args) == 2


@pytest.mark.capture
@pytest.mark.parametrize("pair", [(4, 5), (6, 8), (True, 7), (6, True)])
def test_public_copy_scope_rejects_other_pairs_and_bools(sources, pair):
    root = sources[0]
    frame = decode_artifact(
        load_artifact(
            root / "experiments/edited-sound6-create-001/derived/analysis-001/capture.symbols.npz"
        )
    )
    with pytest.raises(ValueError):
        copy_calibrated_melodic_reference(frame, *pair)


@pytest.mark.capture
def test_last_owner_removal_reproduces_prior_independent_hardware_state(sources):
    root, base, _, reg = sources
    removed = native(excluding_destination_data(base, [6]))
    earlier = decode_artifact(
        load_artifact(
            root / reg["empty_record_model"]["independently_observed_matching_state_artifact"]
        )
    )
    assert removed.encoded_body == earlier.encoded_body
    checks, fits, observed = unshared_checks(base, removed, reg)
    assert all(checks.values()) and fits["entire_empty_record_model_matches"]
    assert not fits["full_codes_retained_under_owner6"]
    assert observed["changed_selector_ids"] == [6] and observed["packet_count_delta"] == -136


@pytest.mark.capture
def test_zero_endpoint_with_retained_full_buffer_is_distinguished_from_removal(sources):
    _, base, _, reg = sources
    packets = list(base.packets)
    index = sound_groups(base)[6][0]
    data = packets[index].payload
    packets[index] = Packet(0xEF78, data[:4] + bytes(4) + data[8:])
    checks, fits, _ = unshared_checks(base, native(packets), reg)
    assert all(checks.values()) and fits["full_codes_retained_under_owner6"]
    assert not fits["sound7_record_is_empty"] and not fits["entire_empty_record_model_matches"]


@pytest.mark.capture
def test_stale_capture_and_changed_pattern_fail_last_owner_core_checks(sources):
    _, base, _, reg = sources
    checks, _, _ = unshared_checks(base, base, reg)
    assert not checks["state_changed_from_baseline"]
    removed = native(excluding_destination_data(base, [6]))
    data = bytearray(pattern_data(removed, 1))
    data[905] = 16
    checks, fits, _ = unshared_checks(
        base, native(_replace_pattern_data(removed, 1, bytes(data))), reg
    )
    assert (
        not checks["all_patterns_unchanged"] and not fits["all_non_sound7_plain_packets_unchanged"]
    )
