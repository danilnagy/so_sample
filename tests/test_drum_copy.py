"""Verify drum-copy locality, retain failed alternatives, and prevent slot mislabeling."""

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
from scripts.check_drum_copy_control import comparison_checks


@pytest.fixture(scope="module")
def drum_copy():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-015-b-copy-sound1-to-drum9"
    registration = json.loads((root / "experiments/drum9-copy-predictions-001.json").read_text())
    capture = directory / "capture.wav"
    artifact = directory / "derived/analysis-001/capture.symbols.npz"
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine first drum-copy capture required")
    assert (
        sha256_file(capture) == "9bafc45f6e12bae5cdcb1c80f60b57248cd3003144946dbf2b670cd20be7a34c"
    )
    base = decode_artifact(load_artifact(directory / registration["baseline_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    return base, actual, registration, capture, artifact


@pytest.mark.capture
def test_drum_copy_preserves_all_existing_data_and_rejects_first_group_only_hypothesis(drum_copy):
    base, actual, registration, _, _ = drum_copy
    checks, hypotheses, changed, records = comparison_checks(base, actual, registration)
    assert all(checks.values()) and changed == list(range(8, 24))
    assert hypotheses == {
        "sound9_uses_selector_block8_to23": True,
        "only_first_destination_group_populated": False,
        "all16_destination_groups_populated": True,
        "populated_destination_records_are_owner0_references": True,
    }
    assert len(actual.packets) - len(base.packets) == 16
    assert len(actual.encoded_body) - len(base.encoded_body) == 224
    assert all(r["bytes"] == 9 and r["owner_id"] == 0 for r in records)


@pytest.mark.capture
@pytest.mark.parametrize("damage", ["pattern", "backing_codes", "opaque_packet"])
def test_checksum_valid_unrelated_changes_fail_locality(drum_copy, damage):
    base, actual, registration, _, _ = drum_copy
    packets = list(actual.packets)
    if damage == "opaque_packet":
        packets.insert(sound_groups(actual)[8][0], Packet(0x1234, b"new opaque data"))
    else:
        index, offset = (4, 6) if damage == "pattern" else (sound_groups(actual)[0][0], 20)
        payload = bytearray(packets[index].payload)
        payload[offset] ^= 1
        packets[index] = Packet(packets[index].tag, bytes(payload))
    altered = decode_frame(bytes(4095) + encode_packets(packets))
    checks, _, _, _ = comparison_checks(base, altered, registration)
    assert checks["all_native_checksums"] and not checks["every_other_plain_packet_unchanged"]
    assert not all(checks.values())


@pytest.mark.capture
def test_unknown_reference_layout_fails_only_its_shape_hypothesis_and_stays_raw(drum_copy):
    base, actual, registration, _, _ = drum_copy
    packets = list(actual.packets)
    index = sound_groups(actual)[8][0]
    payload = packets[index].payload + b"\xff"
    packets[index] = Packet(0xEF78, payload)
    altered = decode_frame(bytes(4095) + encode_packets(packets))
    checks, hypotheses, _, records = comparison_checks(base, altered, registration)
    assert (
        all(checks.values())
        and not hypotheses["populated_destination_records_are_owner0_references"]
    )
    assert records[0]["payload_hex"] == payload.hex() and "owner_id" not in records[0]
    view = drum_sound_view(altered, 9)
    assert view["slice_records"][0]["data_hex"] == payload.hex()
    assert "raw_reference_fields" not in view["slice_records"][0]


@pytest.mark.capture
def test_sound9_aggregates_all16_records_without_mislabeling_them_as_sounds10_to16(drum_copy):
    actual = drum_copy[1]
    view = drum_sound_view(actual, 9)
    assert view["selector_ids"] == list(range(8, 24))
    assert len(view["raw_packet_indices"]) == 16 and view["data_payload_bytes"] == 144
    assert [r["raw_reference_fields"]["second_u32le"] for r in view["slice_records"]] == [
        4044 * (i + 1) for i in range(16)
    ]
    assert view["slice_records"][0]["keyboard_order_status"] == "observed_key1_trim_control"
    assert view["slice_records"][0]["keyboard_key"] == 1
    assert view["slice_records"][1]["keyboard_order_status"] == "observed_key2_trim_control"
    assert view["slice_records"][1]["keyboard_key"] == 2
    assert all(r["keyboard_order_status"] == "unverified" for r in view["slice_records"][2:])
    sound10 = drum_sound_view(actual, 10)
    assert sound10["selector_mapping_status"] == "observed_sound10_copy_block"
    assert not sound10["raw_packet_indices"]
    assert not set(sound10["selector_ids"]) & set(view["selector_ids"])
    for slot in range(11, 17):
        other = drum_sound_view(actual, slot)
        assert "raw_packet_indices" not in other
        assert not other["candidate_raw_packet_indices"]
        assert not set(other["candidate_selector_ids"]) & set(view["selector_ids"])


@pytest.mark.capture
def test_export_contains_all_drum9_records_and_exact_original_packets_without_drum_previews(
    drum_copy, tmp_path
):
    _, actual, _, capture, artifact = drum_copy
    before = sha256_file(capture), sha256_file(artifact)
    output = tmp_path / "drum-project"
    assert (
        main(
            [
                "export-project",
                str(artifact),
                "--capture",
                str(capture),
                "--calibrated-windows",
                "--out-dir",
                str(output),
            ]
        )
        == 0
    )
    sounds = json.loads((output / "sounds.json").read_text())
    assert sounds["schema_version"] == 2
    assert sounds["sounds"][8]["data_payload_bytes"] == 144
    assert len(sounds["sounds"][8]["slice_records"]) == 16
    report = json.loads((output / "export-report.json").read_text())
    assert report["preview_sound_slots"] == [1, 2, 3, 8]
    assert report["hardware_verified"] is False
    view = json.loads((output / "source/packets.json").read_text())
    assert packets_from_view(view) == actual.packets
    for name, record in report["files"].items():
        assert sha256_file(output / name) == record["sha256"]
    assert before == (sha256_file(capture), sha256_file(artifact))
