"""Verify independent key2 calibration, compatible two-slice guards and its first candidate."""

import json
from pathlib import Path

import numpy as np
import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.edits import apply_plan
from po33_re.formats.drums import replace_calibrated_drum_slice_end
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets, sound_data
from po33_re.formats.samples import decode_signed_mulaw, extract_calibrated_drum_slice_sound
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_key2_control import comparison_checks
from scripts.make_drum_key2_candidate import run


@pytest.fixture(scope="module")
def key2_control():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-017-b-drum9-key2-trim-min"
    capture = directory / "capture.wav"
    artifact = directory / "derived/analysis-001/capture.symbols.npz"
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine key2 nonzero-start minimum required")
    assert (
        sha256_file(capture) == "78f321ce42b7cfca70013487b70c62db4bd3dac57c27f7cb9f9a4c2de35692b6"
    )
    registration = json.loads(
        (root / "experiments/drum9-key2-trim-min-predictions-001.json").read_text()
    )
    base = decode_artifact(load_artifact(directory / registration["baseline_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    return base, actual, registration, artifact, capture


@pytest.mark.capture
def test_key2_mapping_exact_endpoint_and_preservation_pass_while_length_prediction_fails(
    key2_control,
):
    checks, fits, packets, selectors, changes, values = comparison_checks(*key2_control[:3])
    assert all(checks.values()) and packets == [385] and selectors == [9]
    assert [c["offset"] for c in changes] == [4, 5]
    assert values["after"] == {"first_u32le": 4045, "second_u32le": 4172, "owner_id": 0}
    assert fits == {
        "key2_maps_to_selector9": True,
        "first_field_unchanged": True,
        "second_field_is_length": False,
        "second_field_is_endpoint": True,
        "second_field_moves_lower_but_above_first": True,
    }


@pytest.mark.capture
def test_key2_writer_reproduces_both_complete_genuine_bodies_and_preserves_accepted_key1(
    key2_control,
):
    base, actual, _, _, _ = key2_control
    assert (
        encode_packets(replace_calibrated_drum_slice_end(base, 9, 2, 4172)) == actual.encoded_body
    )
    assert (
        encode_packets(replace_calibrated_drum_slice_end(actual, 9, 2, 8088)) == base.encoded_body
    )
    packets = replace_calibrated_drum_slice_end(actual, 9, 2, 6045)
    edited = decode_frame(bytes(4095) + encode_packets(packets))
    assert sound_data(edited, 8) == sound_data(actual, 8) == bytes.fromhex("00000000d007000000")
    assert sound_data(edited, 0) == sound_data(actual, 0)


@pytest.mark.capture
@pytest.mark.parametrize("endpoint", [2000, 4171, 8089, True, 6045.0])
def test_key2_rejects_key1_bounds_and_wrong_types(key2_control, endpoint):
    with pytest.raises(ValueError):
        replace_calibrated_drum_slice_end(key2_control[1], 9, 2, endpoint)


@pytest.mark.capture
def test_valid_checksum_nearby_endpoint_does_not_replace_the_exact_registered_prediction(
    key2_control,
):
    base, actual, registration, _, _ = key2_control
    nearby = decode_frame(
        bytes(4095) + encode_packets(replace_calibrated_drum_slice_end(actual, 9, 2, 4173))
    )
    checks, fits, _, _, _, _ = comparison_checks(base, nearby, registration)
    assert all(checks.values()) and fits["second_field_moves_lower_but_above_first"]
    assert not fits["second_field_is_endpoint"] and not fits["second_field_is_length"]


@pytest.mark.capture
def test_changed_first_slice_does_not_pass_key2_mapping_even_with_valid_locality(key2_control):
    base, _, registration, _, _ = key2_control
    wrong = decode_frame(
        bytes(4095) + encode_packets(replace_calibrated_drum_slice_end(base, 9, 1, 127))
    )
    checks, fits, _, selectors, _, _ = comparison_checks(base, wrong, registration)
    assert all(checks.values()) and selectors == [8]
    assert not fits["key2_maps_to_selector9"] and not fits["first_field_unchanged"]


@pytest.mark.capture
def test_key2_preview_is_exact_nonzero_raw_slice_without_pitch_or_gain(key2_control):
    frame = key2_control[1]
    audio, report = extract_calibrated_drum_slice_sound(frame, 9, 2)
    raw = np.frombuffer(sound_data(frame, 0)[9:], dtype=np.uint8)
    assert np.array_equal(audio, decode_signed_mulaw(raw[4045:4172]))
    assert len(audio) == report["preview_code_count"] == 127
    assert report["selector_id"] == 9 and report["pitch_and_gain_applied"] is False


@pytest.mark.capture
def test_two_slice_plan_operations_compose_without_forcing_neighbor_to_original_endpoint(
    key2_control,
):
    _, actual, _, path, _ = key2_control
    source = load_artifact(path)
    unchanged = source.to_bytes()
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(path),
        "source_body_sha256": "09c5f71aad53947f1399cd3080a67a9c6f1ffb8a8fcc5df3dbd6102ac770450f",
        "operations": [
            {"operation": "set_drum_slice_end", "sound": 9, "slice": 1, "end": 1000},
            {"operation": "set_drum_slice_end", "sound": 9, "slice": 2, "end": 6045},
        ],
    }
    edited, trace = apply_plan(source, sha256_file(path), plan)
    frame = decode_artifact(edited)
    assert [i for i, (a, b) in enumerate(zip(actual.packets, frame.packets)) if a != b] == [
        383,
        385,
    ]
    assert sound_data(frame, 8).hex() == "00000000e803000000"
    assert sound_data(frame, 9).hex() == "cd0f00009d17000000"
    assert trace[0]["after_body_sha256"] == trace[1]["before_body_sha256"]
    assert source.to_bytes() == unchanged and edited.metadata["hardware_verified"] is False


@pytest.mark.capture
def test_candidate_pipeline_cli_provenance_and_export_scope(key2_control, tmp_path):
    root = Path(__file__).resolve().parents[1]
    plan = root / "experiments/drum9-key2-end-plan-001/plan.json"
    path, capture = key2_control[3:]
    before = sha256_file(path), sha256_file(capture)
    output = tmp_path / "candidate"
    run(plan, output)
    report = json.loads((output / "software-validation.json").read_text())
    assert report["passed"] and all(report["checks"].values()) and not report["hardware_verified"]
    assert (
        report["preview"]["preview_code_count"] == 2000
        and report["preview"]["export_frames"] == 4096
    )
    candidate = root / "experiments/generated-drum9-key2-end-001/restore.wav"
    assert (output / "restore.wav").read_bytes() == candidate.read_bytes()
    cli_artifact, cli_report = tmp_path / "edited.npz", tmp_path / "edit.json"
    assert (
        main(
            [
                "set-drum-slice-end",
                str(path),
                "--sound",
                "9",
                "--slice",
                "2",
                "--end",
                "6045",
                "--out",
                str(cli_artifact),
                "--report",
                str(cli_report),
            ]
        )
        == 0
    )
    provenance = json.loads(cli_report.read_text())
    assert provenance["selector_id"] == 9 and provenance["start_field"] == 4045
    assert (
        decode_artifact(load_artifact(cli_artifact)).encoded_body
        == decode_artifact(load_artifact(output / "edited.symbols.npz")).encoded_body
    )
    project = tmp_path / "project"
    assert (
        main(
            [
                "export-project",
                str(path),
                "--capture",
                str(capture),
                "--calibrated-windows",
                "--calibrated-drum-slices",
                "--out-dir",
                str(project),
            ]
        )
        == 0
    )
    export = json.loads((project / "export-report.json").read_text())
    assert [r["slice_key"] for r in export["preview_drum_slices"]] == [1, 2]
    sound9 = json.loads((project / "sounds.json").read_text())["sounds"][8]
    assert sound9["slice_records"][1]["keyboard_key"] == 2
    assert sound9["slice_records"][1]["preview_file"] == "samples/09-slice-02.wav"
    assert before == (sha256_file(path), sha256_file(capture))
