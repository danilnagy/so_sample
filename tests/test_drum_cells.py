"""Verify observed drum-note encoding and bounded opaque copy/removal plans."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.edits import apply_plan, compile_edit_plan
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import (
    _replace_pattern_data,
    clone_drum_cell,
    pattern_data,
    patterns_report,
    remove_drum_cell,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from po33_re.project import _pattern_view, export_project, packets_from_view
from scripts.check_drum_note_control import comparison_checks
from scripts.make_drum_cell_candidate import run
from scripts.validate_drum_cell_recapture import comparison_checks as restore_checks


def reframed(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def observed_drum_note():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-020-b-drum10-key1-step1"
    capture, artifact = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine Sound10/key1 note capture required")
    assert (
        sha256_file(capture) == "17cc220dfa4c97f06606ad3c131be8f2bc6080fe7a12fc8be27842ca5c118817"
    )
    registration = json.loads((root / "experiments/drum10-note-predictions-001.json").read_text())
    base = decode_artifact(load_artifact(directory / registration["baseline_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    return base, actual, registration, capture, artifact


@pytest.mark.capture
def test_real_drum_note_preservation_and_mapping_pass_but_F0_prediction_fails(observed_drum_note):
    checks, fits, packets, changes, observed = comparison_checks(*observed_drum_note[:3])
    assert all(checks.values()) and packets == [4, 7]
    assert fits["sound10_maps_to_cell10"] and fits["primary_matches_sound3_key1"]
    assert not fits["auxiliary_key1_matches_melodic_F0"] and not fits["primary_matches_sound2_key1"]
    assert (
        observed["candidate_primary_hex"] == "0df883" and observed["candidate_auxiliary_byte"] == 16
    )
    assert [c["offset"] for c in changes] == [27, 28, 29, 777]


@pytest.mark.capture
def test_copy_removal_reproduce_whole_genuine_bodies_and_preserve_both_melodic_neighbors(
    observed_drum_note,
):
    base, actual, _, _, _ = observed_drum_note
    assert encode_packets(remove_drum_cell(actual, 1, 10, [1])) == base.encoded_body
    target = reframed(clone_drum_cell(actual, 1, 10, 1, [9]))
    assert encode_packets(remove_drum_cell(target, 1, 10, [9])) == actual.encoded_body
    only9 = reframed(remove_drum_cell(target, 1, 10, [1]))
    assert encode_packets(clone_drum_cell(only9, 1, 10, 9, [1])) == target.encoded_body
    assert encode_packets(remove_drum_cell(target, 1, 10, [1, 9])) == base.encoded_body
    before, after = pattern_data(actual, 1), pattern_data(target, 1)
    assert before[387:393] == after[387:393] and before[897:899] == after[897:899]
    assert [i for i, (a, b) in enumerate(zip(actual.packets, target.packets)) if a != b] == [5, 7]


@pytest.mark.capture
@pytest.mark.parametrize(
    "pattern,sound,source,targets",
    [
        (2, 10, 1, [9]),
        (True, 10, 1, [9]),
        (1, 9, 1, [9]),
        (1, 10.0, 1, [9]),
        (1, 10, True, [9]),
        (1, 10, 2, [9]),
        (1, 10, 1, [1]),
        (1, 10, 1, [9, 9]),
        (1, 10, 1, [True]),
        (1, 10, 1, []),
    ],
)
def test_unsupported_context_empty_source_and_invalid_targets_rejected(
    observed_drum_note, pattern, sound, source, targets
):
    with pytest.raises(ValueError):
        clone_drum_cell(observed_drum_note[1], pattern, sound, source, targets)


@pytest.mark.capture
def test_occupied_drum_target_and_empty_removal_rejected(observed_drum_note):
    actual = observed_drum_note[1]
    target = reframed(clone_drum_cell(actual, 1, 10, 1, [9]))
    with pytest.raises(ValueError, match="occupied"):
        clone_drum_cell(target, 1, 10, 1, [9])
    with pytest.raises(ValueError):
        remove_drum_cell(actual, 1, 10, [9])
    with pytest.raises(ValueError):
        remove_drum_cell(actual, 1, 10, [1, 1])


@pytest.mark.capture
@pytest.mark.parametrize(
    "damage",
    [
        "drum_primary",
        "melodic_F0_auxiliary",
        "other_drum_slice",
        "sound2_neighbor",
        "sound3_neighbor",
        "foreign_cell",
        "copied_window",
        "sample_neighbor",
    ],
)
def test_unobserved_note_or_sample_context_rejected(observed_drum_note, damage):
    actual = observed_drum_note[1]
    if damage in ("copied_window", "sample_neighbor"):
        packets = list(actual.packets)
        index = 415 if damage == "copied_window" else 417
        payload = bytearray(packets[index].payload)
        payload[4] ^= 1
        packets[index] = Packet(packets[index].tag, bytes(payload))
        altered = reframed(packets)
    else:
        data = bytearray(pattern_data(actual, 1))
        if damage == "melodic_F0_auxiliary":
            data[777] = 0xF0
        elif damage == "other_drum_slice":
            data[777] = 0x11
        else:
            index = {
                "drum_primary": 27,
                "sound2_neighbor": 388,
                "sound3_neighbor": 6,
                "foreign_cell": 30,
            }[damage]
            data[index] ^= 1
        altered = reframed(_replace_pattern_data(actual, 1, bytes(data)))
    with pytest.raises(ValueError):
        clone_drum_cell(altered, 1, 10, 1, [9])


@pytest.mark.capture
def test_unknown_global_packet_preserved_and_plan_copy_removal_returns_source(observed_drum_note):
    actual = observed_drum_note[1]
    packets = list(actual.packets)
    packets[1] = Packet(packets[1].tag, b"opaque future global fields")
    opaque = reframed(packets)
    assert clone_drum_cell(opaque, 1, 10, 1, [9])[1] == opaque.packets[1]
    root = Path(__file__).resolve().parents[1]
    plan = json.loads((root / "experiments/drum-cell-copy-plan-001/plan.json").read_text())
    plan["operations"].append(
        {"operation": "remove_drum_cell", "pattern": 1, "sound": 10, "steps": [9]}
    )
    path = observed_drum_note[4]
    source = load_artifact(path)
    unchanged = source.to_bytes()
    edited, trace = apply_plan(source, sha256_file(path), plan)
    assert decode_artifact(edited).encoded_body == actual.encoded_body
    assert trace[0]["after_body_sha256"] == trace[1]["before_body_sha256"]
    assert source.to_bytes() == unchanged and not edited.metadata["hardware_verified"]


@pytest.mark.capture
def test_candidate_pipeline_exact_reproduction_and_target_checker_rejects_wrong_F0(
    observed_drum_note, tmp_path
):
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "candidate"
    report = run(root / "experiments/drum-cell-copy-plan-001/plan.json", output)
    assert report["passed"] and all(report["checks"].values()) and not report["hardware_verified"]
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments/generated-drum-cell-copy-001/restore.wav"
    ).read_bytes()
    target = decode_artifact(load_artifact(output / "edited.symbols.npz"))
    registration = json.loads(
        (root / "experiments/edited-drum-cell-copy-001/restore-registration.json").read_text()
    )
    checks, packets, changes, steps = restore_checks(
        observed_drum_note[1], target, target, registration
    )
    assert all(checks.values()) and packets == [5, 7] and steps == [1, 9]
    assert [c["offset"] for c in changes] == [411, 412, 413, 905]
    data = bytearray(pattern_data(target, 1))
    data[905] = 0xF0
    wrong = reframed(_replace_pattern_data(target, 1, bytes(data)))
    checks, _, _, _ = restore_checks(observed_drum_note[1], target, wrong, registration)
    assert (
        checks["all_native_checksums"] and checks["all_melodic_sound2_and_sound3_cells_preserved"]
    )
    assert not checks["target_body_matches"] and not checks["observed_raw_drum_pair_preserved"]


@pytest.mark.capture
def test_drum_plan_rejects_extra_key_argument_before_creating_output(observed_drum_note, tmp_path):
    root = Path(__file__).resolve().parents[1]
    plan = json.loads((root / "experiments/drum-cell-copy-plan-001/plan.json").read_text())
    plan["operations"][0]["key"] = 2
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    output = tmp_path / "rejected"
    with pytest.raises(ValueError, match="Unexpected or missing"):
        compile_edit_plan(observed_drum_note[4], plan_path, output)
    assert not output.exists()


@pytest.mark.capture
def test_project_projects_only_observed_drum_pair_and_preserves_all_raw_data(
    observed_drum_note, tmp_path
):
    _, actual, _, capture, artifact = observed_drum_note
    output = tmp_path / "project"
    report = export_project(
        artifact, capture, output, calibrated_windows=True, calibrated_drum_slices=True
    )
    pattern = json.loads((output / "patterns/01.json").read_text())
    drum = [c for c in pattern["observed_cells"] if c["candidate_sound_slot"] == 10]
    assert len(drum) == 1 and drum[0]["step"] == 1 and drum[0]["auxiliary_byte"] == 16
    assert drum[0]["calibrated_drum_slice_key"] == 1 and drum[0]["calibrated_keyboard_key"] is None
    data = bytearray(pattern_data(actual, 1))
    data[777] = 0x12
    unknown = reframed(_replace_pattern_data(actual, 1, bytes(data)))
    view = _pattern_view(unknown, patterns_report(unknown)["patterns"][0])
    unobserved = next(c for c in view["observed_cells"] if c["candidate_sound_slot"] == 10)
    assert unobserved["auxiliary_byte"] == 18 and unobserved["calibrated_drum_slice_key"] is None
    assert (
        packets_from_view(json.loads((output / "source/packets.json").read_text()))
        == actual.packets
    )
    for name, record in report["files"].items():
        assert sha256_file(output / name) == record["sha256"]
