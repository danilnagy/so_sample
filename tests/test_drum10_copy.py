"""Check the independently observed second drum block without inferring key order."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from po33_re.project import drum_sound_view, packets_from_view
from scripts.check_drum10_copy_control import comparison_checks


@pytest.fixture(scope="module")
def drum10_copy():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-018-b-copy-sound1-to-drum10"
    capture = directory / "capture-retry.wav"
    artifact = directory / "derived/analysis-004/capture.symbols.npz"
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine clean Sound10-copy recording required")
    assert (
        sha256_file(capture) == "073011e3cdd30f3bb376396385a154ec581d24412c0f93362d189e2e8126e804"
    )
    registration = json.loads((root / "experiments/drum10-copy-predictions-001.json").read_text())
    base = decode_artifact(load_artifact(directory / registration["baseline_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    return base, actual, registration, capture, artifact


@pytest.mark.capture
def test_sound10_block_exact_autocopy_and_preservation_hypotheses_all_pass(drum10_copy):
    checks, fits, changed, records = comparison_checks(*drum10_copy[:3])
    assert all(checks.values()) and all(fits.values()) and changed == list(range(24, 40))
    assert len(records) == 16 and all(r["bytes"] == 9 and r["owner_id"] == 0 for r in records)
    assert len(drum10_copy[1].packets) == 543 and drum10_copy[1].end_byte == 89844


@pytest.mark.capture
def test_different_destination_boundaries_fail_exact_prediction_but_not_locality(drum10_copy):
    base, actual, registration, _, _ = drum10_copy
    packets = list(actual.packets)
    index = sound_groups(actual)[24][0]
    payload = packets[index].payload[:4] + (4000).to_bytes(4, "little") + b"\0"
    packets[index] = Packet(0xEF78, payload)
    different = decode_frame(bytes(4095) + encode_packets(packets))
    checks, fits, _, _ = comparison_checks(base, different, registration)
    assert all(checks.values()) and fits["sound10_uses_selector_block24_to39"]
    assert not fits["destination_records_equal_original_sound9_autocopy"]


@pytest.mark.capture
@pytest.mark.parametrize("damage", ["pattern", "sound9_slice", "backing_codes"])
def test_checksum_valid_unrelated_changes_fail_sound10_copy_preservation(drum10_copy, damage):
    base, actual, registration, _, _ = drum10_copy
    groups = sound_groups(actual)
    index, offset = (
        (4, 6)
        if damage == "pattern"
        else (groups[8][0], 4)
        if damage == "sound9_slice"
        else (groups[0][0], 20)
    )
    packets = list(actual.packets)
    payload = bytearray(packets[index].payload)
    payload[offset] ^= 1
    packets[index] = Packet(packets[index].tag, bytes(payload))
    different = decode_frame(bytes(4095) + encode_packets(packets))
    checks, _, _, _ = comparison_checks(base, different, registration)
    assert checks["all_native_checksums"] and not checks["every_other_plain_packet_unchanged"]
    assert not all(checks.values())


@pytest.mark.capture
def test_sound10_view_has_all16_records_and_only_independently_mapped_key1(drum10_copy):
    view = drum_sound_view(drum10_copy[1], 10)
    assert view["selector_mapping_status"] == "observed_sound10_copy_block"
    assert view["selector_ids"] == list(range(24, 40)) and view["data_payload_bytes"] == 144
    assert len(view["raw_packet_indices"]) == 16
    assert view["slice_records"][0]["keyboard_key"] == 1
    assert view["slice_records"][0]["keyboard_order_status"] == "observed_key1_slice_copy_control"
    assert all(
        r["keyboard_order_status"] == "unverified" and "keyboard_key" not in r
        for r in view["slice_records"][1:]
    )
    assert (
        drum_sound_view(drum10_copy[1], 11)["selector_mapping_status"]
        == "inferred_other_drum_block_unverified"
    )


@pytest.mark.capture
def test_export_retains_both_drum_blocks_and_existing_previews_without_sound10_audio(
    drum10_copy, tmp_path
):
    _, actual, _, capture, artifact = drum10_copy
    before = sha256_file(capture), sha256_file(artifact)
    output = tmp_path / "project"
    assert (
        main(
            [
                "export-project",
                str(artifact),
                "--capture",
                str(capture),
                "--calibrated-windows",
                "--calibrated-drum-slices",
                "--out-dir",
                str(output),
            ]
        )
        == 0
    )
    sounds = json.loads((output / "sounds.json").read_text())["sounds"]
    assert sounds[9]["data_payload_bytes"] == 144 and len(sounds[9]["slice_records"]) == 16
    report = json.loads((output / "export-report.json").read_text())
    assert [(r["sound_slot"], r["slice_key"]) for r in report["preview_drum_slices"]] == [
        (9, 1),
        (9, 2),
    ]
    assert report["preview_sound_slots"] == [1, 2, 3, 8] and not report["hardware_verified"]
    raw = json.loads((output / "source/packets.json").read_text())
    assert packets_from_view(raw) == actual.packets
    for name, record in report["files"].items():
        assert sha256_file(output / name) == record["sha256"]
    assert before == (sha256_file(capture), sha256_file(artifact))
