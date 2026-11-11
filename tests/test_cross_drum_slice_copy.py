"""Verify observed copy bodies, bounded composition and independent target comparison."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.edits import compile_edit_plan
from po33_re.formats.drums import copy_calibrated_drum_slice, replace_calibrated_drum_slice_end
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from po33_re.project import export_project, packets_from_view
from scripts.check_cross_drum_slice_copy_control import comparison_checks
from scripts.make_cross_drum_slice_candidate import reframed, run
from scripts.validate_cross_drum_slice_recapture import comparison_checks as restore_checks


@pytest.fixture(scope="module")
def physical_copy():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-019-b-copy-drum9-key1-to-drum10-key1"
    capture = directory / "capture.wav"
    artifact = directory / "derived/analysis-001/capture.symbols.npz"
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine physical single-slice copy required")
    assert (
        sha256_file(capture) == "9b2e9d4400a521063629dcf73d1de74972b7deb1a8b956d67f76c0787cf4be1b"
    )
    registration = json.loads(
        (root / "experiments/cross-drum-slice-copy-predictions-001.json").read_text()
    )
    base = decode_artifact(load_artifact(directory / registration["baseline_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    return base, actual, registration, capture, artifact


def changed_packet(frame, index, payload):
    packets = list(frame.packets)
    packets[index] = Packet(packets[index].tag, payload)
    return reframed(packets)


@pytest.mark.capture
def test_all_saved_physical_copy_predictions_and_preservation_pass(physical_copy):
    checks, fits, packets, selectors, changes, values = comparison_checks(*physical_copy[:3])
    assert all(checks.values()) and all(fits.values())
    assert packets == [415] and selectors == [24] and [c["offset"] for c in changes] == [4, 5]
    assert values["after"] == {"first_u32le": 0, "second_u32le": 2000, "owner_id": 0}


@pytest.mark.capture
def test_wrong_destination_mapping_does_not_pass_even_with_verbatim_source_copy(physical_copy):
    base, _, registration, _, _ = physical_copy
    wrong = changed_packet(base, 417, base.packets[383].payload)
    checks, fits, _, selectors, _, _ = comparison_checks(base, wrong, registration)
    assert all(checks.values()) and selectors == [25]
    assert fits["reference_copied_verbatim_from_source_key1"]
    assert not fits["destination_key1_maps_to_selector24"]


@pytest.mark.capture
@pytest.mark.parametrize("index,offset", [(4, 6), (383, 4), (385, 0), (417, 4), (111, 20)])
def test_checksum_valid_unrelated_changes_fail_preservation(physical_copy, index, offset):
    base, actual, registration, _, _ = physical_copy
    payload = bytearray(actual.packets[index].payload)
    payload[offset] ^= 1
    altered = changed_packet(actual, index, bytes(payload))
    checks, _, _, _, _, _ = comparison_checks(base, altered, registration)
    assert checks["all_native_checksums"] and not checks["every_other_plain_packet_unchanged"]


@pytest.mark.capture
def test_writer_reproduces_complete_genuine_forward_and_inverse_bodies(physical_copy):
    base, actual, _, _, _ = physical_copy
    assert encode_packets(copy_calibrated_drum_slice(base, 9, 1, 10, 1)) == actual.encoded_body
    inverse = reframed(replace_calibrated_drum_slice_end(actual, 9, 1, 4044))
    inverse = reframed(copy_calibrated_drum_slice(inverse, 9, 1, 10, 1))
    inverse = reframed(replace_calibrated_drum_slice_end(inverse, 9, 1, 2000))
    assert inverse.encoded_body == base.encoded_body
    opaque = changed_packet(actual, 1, b"opaque global fields remain intact")
    edited = copy_calibrated_drum_slice(opaque, 9, 2, 10, 1)
    assert edited[1] == opaque.packets[1]
    assert [i for i, (a, b) in enumerate(zip(edited, opaque.packets)) if a != b] == [415]


@pytest.mark.capture
@pytest.mark.parametrize(
    "arguments",
    [
        (10, 1, 10, 1),
        (9, 3, 10, 1),
        (9, True, 10, 1),
        (9, 1, 9, 1),
        (9, 1, 11, 1),
        (9, 1, 10, 2),
        (9, 1, 10, True),
        (9, 1, 10.0, 1),
    ],
)
def test_unsupported_copy_mappings_and_types_are_rejected(physical_copy, arguments):
    with pytest.raises(ValueError):
        copy_calibrated_drum_slice(physical_copy[1], *arguments)


@pytest.mark.capture
@pytest.mark.parametrize(
    "damage",
    [
        "source_start",
        "source_owner",
        "source_other",
        "owner_shape",
        "owner_start",
        "destination_start",
        "destination_end",
        "destination_owner",
        "destination_shape",
        "destination_neighbor",
        "destination_empty",
        "destination_multiple",
    ],
)
def test_unknown_source_or_destination_context_is_rejected(physical_copy, damage):
    frame = physical_copy[1]
    groups = sound_groups(frame)
    index = (
        groups[8][0]
        if damage.startswith("source")
        else groups[0][0]
        if damage.startswith("owner")
        else groups[24][0]
    )
    if damage == "source_other":
        index = groups[10][0]
    if damage == "destination_neighbor":
        index = groups[25][0]
    payload = bytearray(frame.packets[index].payload)
    if damage in (
        "source_start",
        "source_other",
        "owner_start",
        "destination_start",
        "destination_neighbor",
    ):
        payload[0] ^= 1
    elif damage in ("source_owner", "destination_owner"):
        payload[8] = 1
    elif damage == "destination_end":
        payload[4:8] = (79).to_bytes(4, "little")
    elif damage == "owner_shape":
        payload.pop()
    elif damage == "destination_shape":
        payload.append(0)
    elif damage == "destination_empty":
        payload.clear()
    packets = list(frame.packets)
    packets[index] = Packet(frame.packets[index].tag, bytes(payload))
    if damage == "destination_multiple":
        packets.insert(index + 1, Packet(0xEF78, b"extra"))
    altered = decode_frame(bytes(4095) + encode_packets(packets))
    with pytest.raises(ValueError):
        copy_calibrated_drum_slice(altered, 9, 2, 10, 1)


@pytest.mark.capture
def test_candidate_reproduces_registered_wav_and_target_validator_rejects_near_miss(
    physical_copy, tmp_path
):
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "candidate"
    report = run(root / "experiments/drum-slice-copy-plan-001/plan.json", output)
    assert report["passed"] and all(report["checks"].values()) and not report["hardware_verified"]
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments/generated-drum-slice-copy-001/restore.wav"
    ).read_bytes()
    target = decode_artifact(load_artifact(output / "edited.symbols.npz"))
    registration = json.loads(
        (root / "experiments/edited-drum-slice-copy-001/restore-registration.json").read_text()
    )
    checks, packets, selectors, _, _ = restore_checks(
        physical_copy[1], target, target, registration
    )
    assert all(checks.values()) and packets == [415] and selectors == [24]
    payload = bytearray(target.packets[415].payload)
    payload[4] ^= 1
    near = changed_packet(target, 415, bytes(payload))
    checks, _, _, _, _ = restore_checks(physical_copy[1], target, near, registration)
    assert checks["every_other_plain_packet_unchanged"] and checks["all_native_checksums"]
    assert not checks["target_body_matches"] and not checks["expected_reference_byte_changes"]


@pytest.mark.capture
def test_copy_plan_rejects_extra_arguments_before_creating_output(physical_copy, tmp_path):
    root = Path(__file__).resolve().parents[1]
    plan = json.loads((root / "experiments/drum-slice-copy-plan-001/plan.json").read_text())
    plan["operations"][0]["allow_allocation"] = True
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    output = tmp_path / "rejected"
    with pytest.raises(ValueError, match="Unexpected or missing"):
        compile_edit_plan(physical_copy[4], plan_path, output)
    assert not output.exists()


@pytest.mark.capture
def test_export_maps_only_sound10_key1_and_previews_its_accepted_zero_start_copy(
    physical_copy, tmp_path
):
    _, actual, _, capture, artifact = physical_copy
    output = tmp_path / "project"
    export_project(artifact, capture, output, calibrated_windows=True, calibrated_drum_slices=True)
    sounds = json.loads((output / "sounds.json").read_text())["sounds"]
    records = sounds[9]["slice_records"]
    assert records[0]["keyboard_key"] == 1 and records[0]["data_hex"] == "00000000d007000000"
    assert all("keyboard_key" not in r for r in records[1:])
    report = json.loads((output / "export-report.json").read_text())
    assert [(r["sound_slot"], r["slice_key"]) for r in report["preview_drum_slices"]] == [
        (9, 1),
        (9, 2),
        (10, 1),
    ]
    assert (output / "samples/10-slice-01.wav").read_bytes() == (
        output / "samples/09-slice-01.wav"
    ).read_bytes()
    assert (
        packets_from_view(json.loads((output / "source/packets.json").read_text()))
        == actual.packets
    )
    for name, record in report["files"].items():
        assert sha256_file(output / name) == record["sha256"]
