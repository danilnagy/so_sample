"""Check the genuine shared reference and keep future overwrite policies independent."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_data,
)
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from po33_re.project import export_project, packets_from_view
from scripts.check_second_owner_copy_control import comparison_checks as copy_checks
from scripts.check_shared_owner_rerecord import comparison_checks, zero_start_window


@pytest.fixture(scope="module")
def shared_copy():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-023-b-copy-sound4-to-sound5"
    artifact = directory / "derived/analysis-003/capture.symbols.npz"
    capture = directory / "capture.wav"
    if not artifact.exists() or not capture.exists():
        pytest.skip("Genuine second-owner copy required")
    assert (
        sha256_file(capture)
        == sha256_file(directory / "po_33_61.wav")
        == "9cf4096737c90537a7dacbb0d4f4436c8730958468a7313eee97e73d5ed0c387"
    )
    frames = [
        decode_artifact(load_artifact(directory / f"derived/analysis-{n:03}/capture.symbols.npz"))
        for n in (3, 4, 5)
    ]
    assert frames[0].encoded_body == frames[1].encoded_body == frames[2].encoded_body
    copy = json.loads((root / "experiments/sound4-to5-copy-predictions-001.json").read_text())
    base = decode_artifact(load_artifact(directory / copy["baseline_artifact"]))
    rerecord = json.loads(
        (root / "experiments/shared-sound4-rerecord-predictions-001.json").read_text()
    )
    return base, frames[0], copy, rerecord, capture, artifact


def rerecorded(frame, policy):
    old = sound_data(frame, 3)
    new = bytes(4) + (50000).to_bytes(4, "little") + b"\x03" + b"\x55" * 65536
    replacement = {3: new}
    if policy == "transfer":
        replacement[4] = old[:8] + b"\x04" + old[9:]
    elif policy == "lost_copy":
        replacement[4] = b""
    packets, selector = [], None
    for packet in frame.packets:
        if packet.tag == 0x68B5:
            selector = packet.payload[0]
            packets.append(packet)
            if selector in replacement:
                data = replacement[selector]
                packets.extend(Packet(0xEF78, data[i : i + 255]) for i in range(0, len(data), 255))
        elif packet.tag != 0xEF78 or selector not in replacement:
            packets.append(packet)
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.mark.capture
def test_genuine_copy_preserves_both_owners_and_adds_only_owner3_reference(shared_copy):
    checks, fits, changed, records = copy_checks(*shared_copy[:3])
    assert all(checks.values()) and changed == [4]
    assert fits["destination_is_exact_owner3_reference"] and fits["one_new_reference_packet_only"]
    assert not fits["destination_is_duplicate_self_owned_buffer"]
    assert records[0]["payload_hex"] == "00000000c06f000003"


@pytest.mark.capture
def test_copy_on_write_transfer_and_shared_overwrite_are_separate_testable_policies(shared_copy):
    base, registration = shared_copy[1], shared_copy[3]
    for policy in ("transfer", "shared"):
        checks, fits, changed, _, observed = comparison_checks(
            base, rerecorded(base, policy), registration
        )
        assert all(checks.values()) and fits["new_sound4_backing_buffer_is_larger"]
        assert fits["sound5_logical_sample_window_preserved"] is (policy == "transfer")
        assert fits["old_full_buffer_transferred_to_self_owned_sound5"] is (policy == "transfer")
        assert fits["sound5_reference_unchanged_and_tracks_new_sound4"] is (policy == "shared")
        assert changed == ([3, 4] if policy == "transfer" else [3])
        assert observed["sound4_after_window"]["backing_code_count"] == 65536


@pytest.mark.capture
def test_copy_loss_is_reported_without_rejecting_the_valid_recording_as_corrupt(shared_copy):
    base, registration = shared_copy[1], shared_copy[3]
    checks, fits, _, _, observed = comparison_checks(
        base, rerecorded(base, "lost_copy"), registration
    )
    assert all(checks.values()) and not fits["sound5_record_remains_present"]
    assert not fits["sound5_logical_sample_window_preserved"]
    assert not observed["sound5_after_window"]["resolved"]


@pytest.mark.capture
def test_unresolved_window_is_not_guessed_from_expected_owner(shared_copy):
    base, registration = shared_copy[1], shared_copy[3]
    frame = rerecorded(base, "transfer")
    packets = list(frame.packets)
    index = next(i for i, p in enumerate(packets) if p == Packet(0x68B5, b"\x03")) + 1
    payload = bytearray(packets[index].payload)
    payload[0] = 1
    packets[index] = Packet(packets[index].tag, bytes(payload))
    unknown = decode_frame(bytes(4095) + encode_packets(packets))
    checks, fits, _, _, observed = comparison_checks(base, unknown, registration)
    assert all(checks.values()) and not fits["new_sound4_record_is_zero_start"]
    assert not observed["sound4_after_window"]["resolved"]
    assert zero_start_window({}, 3)[0] is None


@pytest.mark.capture
def test_no_re_recording_or_changed_patterns_do_not_pass_control(shared_copy):
    base, registration = shared_copy[1], shared_copy[3]
    checks, _, _, _, _ = comparison_checks(base, base, registration)
    assert not checks["source_sound4_record_changed"]
    frame = rerecorded(base, "transfer")
    data = bytearray(pattern_data(frame, 1))
    data[905] = 16
    different = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(frame, 1, bytes(data)))
    )
    checks, _, _, _, _ = comparison_checks(base, different, registration)
    assert checks["all_native_checksums"] and not checks["all_patterns_unchanged"]


@pytest.mark.capture
def test_project_preserves_shared_codes_and_identical_sound4_and5_previews(shared_copy, tmp_path):
    _, actual, _, _, capture, artifact = shared_copy
    output = tmp_path / "project"
    report = export_project(
        artifact, capture, output, calibrated_windows=True, calibrated_drum_slices=True
    )
    assert report["preview_sound_slots"] == [1, 2, 3, 4, 5, 8] and len(report["files"]) == 31
    assert (output / "samples/04.wav").read_bytes() == (output / "samples/05.wav").read_bytes()
    assert (
        packets_from_view(json.loads((output / "source/packets.json").read_text()))
        == actual.packets
    )
    for name, record in report["files"].items():
        assert sha256_file(output / name) == record["sha256"]
