"""Verify the observed drum key1 mapping, local endpoint guards and candidate roundtrip."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.formats.drums import replace_calibrated_drum_slice_end
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_slice_control import comparison_checks
from scripts.make_drum_slice_candidate import run


@pytest.fixture(scope="module")
def drum_minimum():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-016-b-drum9-key1-trim-min"
    capture, artifact = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine first drum-slice trim recording required")
    assert (
        sha256_file(capture) == "bb5cbcd9cee52cd390dcc9f5e33f1fec719891d951d4d92ae21d3dae1a924046"
    )
    registration = json.loads(
        (root / "experiments/drum9-key1-trim-min-predictions-001.json").read_text()
    )
    original = decode_artifact(load_artifact(directory / registration["baseline_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    return original, actual, registration, artifact


def altered_packet(frame, index, payload):
    packets = list(frame.packets)
    packets[index] = Packet(packets[index].tag, payload)
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.mark.capture
def test_key1_mapping_passes_but_exact_melodic_minimum_prediction_remains_failed(drum_minimum):
    original, actual, registration, _ = drum_minimum
    checks, fits, packets, selectors, changes, values = comparison_checks(
        original, actual, registration
    )
    assert all(checks.values()) and packets == [383] and selectors == [8]
    assert [c["offset"] for c in changes] == [4, 5]
    assert fits == {
        "key1_maps_to_selector8": True,
        "first_field_unchanged_zero": True,
        "second_field_is_zero_start_melodic_minimum": False,
        "second_field_moves_lower": True,
    }
    assert values["after"] == {"first_u32le": 0, "second_u32le": 127, "owner_id": 0}


@pytest.mark.capture
def test_writer_reproduces_both_complete_genuine_bodies_and_preserves_opaque_packet(drum_minimum):
    original, actual, _, _ = drum_minimum
    assert (
        encode_packets(replace_calibrated_drum_slice_end(original, 9, 1, 127))
        == actual.encoded_body
    )
    assert (
        encode_packets(replace_calibrated_drum_slice_end(actual, 9, 1, 4044))
        == original.encoded_body
    )
    opaque = altered_packet(actual, 1, b"unknown future global data")
    packets = replace_calibrated_drum_slice_end(opaque, 9, 1, 2000)
    assert packets[1] == opaque.packets[1]
    assert [i for i, (a, b) in enumerate(zip(opaque.packets, packets)) if a != b] == [383]


@pytest.mark.capture
@pytest.mark.parametrize("endpoint", [79, 126, 4045, 65535, True, 2000.0])
def test_writer_rejects_uncalibrated_endpoints_and_types(drum_minimum, endpoint):
    with pytest.raises(ValueError):
        replace_calibrated_drum_slice_end(drum_minimum[1], 9, 1, endpoint)


@pytest.mark.capture
@pytest.mark.parametrize("slot,key", [(10, 1), (9, 3), (True, 1), (9, True)])
def test_only_sound9_and_directly_controlled_keys_are_supported(drum_minimum, slot, key):
    with pytest.raises(ValueError):
        replace_calibrated_drum_slice_end(drum_minimum[1], slot, key, 2000)


@pytest.mark.capture
@pytest.mark.parametrize(
    "damage",
    [
        "start",
        "owner",
        "shape",
        "other_slice",
        "owner_start",
        "owner_self",
        "owner_size",
        "multiple_slices",
    ],
)
def test_unknown_context_and_multiple_changed_slices_are_rejected(drum_minimum, damage):
    original, actual, registration, _ = drum_minimum
    groups = sound_groups(actual)
    index = groups[8][0]
    payload = bytearray(actual.packets[index].payload)
    if damage == "start":
        payload[0] = 1
    elif damage == "owner":
        payload[8] = 1
    elif damage == "shape":
        payload = payload[:-1]
    elif damage in ("other_slice", "multiple_slices"):
        index = groups[9][0]
        payload = bytearray(actual.packets[index].payload)
        payload[4] ^= 1
    else:
        index = groups[0][0]
        payload = bytearray(actual.packets[index].payload)
        if damage == "owner_start":
            payload[0] = 1
        elif damage == "owner_self":
            payload[8] = 1
        else:
            payload = payload[:-1]
    altered = altered_packet(actual, index, bytes(payload))
    unchanged = altered.encoded_body
    with pytest.raises(ValueError):
        replace_calibrated_drum_slice_end(altered, 9, 1, 2000)
    assert altered.encoded_body == unchanged
    if damage == "multiple_slices":
        checks, _, _, selectors, _, _ = comparison_checks(original, altered, registration)
        assert checks["all_native_checksums"] and selectors == [8, 9]
        assert not checks["exactly_one_sound9_reference_changed"]


@pytest.mark.capture
def test_registered_candidate_pipeline_and_cli_preserve_inputs_and_refuse_aliases(
    drum_minimum, tmp_path
):
    root = Path(__file__).resolve().parents[1]
    plan = root / "experiments/drum9-slice-end-plan-001/plan.json"
    source = drum_minimum[3]
    unchanged = source.read_bytes()
    output = tmp_path / "candidate"
    run(plan, output)
    report = json.loads((output / "software-validation.json").read_text())
    assert report["passed"] and all(report["checks"].values())
    assert report["hardware_verified"] is False
    assert report["expected_reference_hex"] == "00000000d007000000"
    assert (
        report["preview"]["raw_code_count"] == 2000 and report["preview"]["export_frames"] == 4096
    )
    accepted_candidate = root / "experiments/generated-drum9-slice-end-001/restore.wav"
    assert (output / "restore.wav").read_bytes() == accepted_candidate.read_bytes()
    edited, edit_report = tmp_path / "edited.npz", tmp_path / "edited.json"
    args = [
        "set-drum-slice-end",
        str(source),
        "--sound",
        "9",
        "--slice",
        "1",
        "--end",
        "2000",
        "--out",
        str(edited),
        "--report",
        str(edit_report),
    ]
    assert main(args) == 0
    assert (
        decode_artifact(load_artifact(edited)).encoded_body
        == decode_artifact(load_artifact(output / "edited.symbols.npz")).encoded_body
    )
    assert json.loads(edit_report.read_text())["slice_key"] == 1
    assert main(args) == 2
    assert main(args[: args.index("--out")] + ["--out", str(source), "--force"]) == 2
    with pytest.raises(ValueError):
        run(plan, output)
    assert source.read_bytes() == unchanged
