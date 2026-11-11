"""Verify the physical key2 result and keep allocation hypotheses independent."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from po33_re.project import export_project, packets_from_view
from scripts.check_drum_note_key_control import comparison_checks as key_checks
from scripts.check_sample_allocation_control import comparison_checks


def reframed(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def key2_capture():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-021-b-drum10-step9-key2"
    capture, artifact = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine Sound10/key2 note capture required")
    assert (
        sha256_file(capture) == "853d6d6249a98538ab4200b1067d216636b6e796044dc01bf1993c2b80061114"
    )
    registration = json.loads(
        (root / "experiments/drum10-step9-key2-predictions-001.json").read_text()
    )
    base = decode_artifact(load_artifact(directory / registration["baseline_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    allocation = json.loads(
        (root / "experiments/sound4-allocation-predictions-001.json").read_text()
    )
    return base, actual, registration, allocation, capture, artifact


def with_sound4(frame, *, owner=3, code_count=37):
    # Deliberately non-power-of-two synthetic size: no geometry rule is assumed.
    payload = bytes(4) + code_count.to_bytes(4, "little") + bytes([owner]) + b"\x55" * code_count
    packets = list(frame.packets)
    selector = next(i for i, p in enumerate(packets) if p == Packet(0x68B5, b"\x03"))
    packets.insert(selector + 1, Packet(0xEF78, payload))
    return reframed(packets)


@pytest.mark.capture
def test_real_key2_changes_only_auxiliary905_to11_and_preserves_all_other_state(key2_capture):
    checks, fits, packets, changes, observed = key_checks(*key2_capture[:3])
    assert all(checks.values()) and packets == [7]
    assert changes == [{"offset": 905, "old": 16, "new": 17}]
    assert fits["auxiliary_preserves_drum_upper_nibble_and_increments_key"]
    assert not fits["auxiliary_matches_melodic_key2"] and observed["after_auxiliary_byte"] == 17


@pytest.mark.capture
def test_new_independent_buffer_can_pass_without_any_assumed_padding_size(key2_capture):
    base, registration = key2_capture[1], key2_capture[3]
    frame = with_sound4(base)
    checks, fits, changed, records, observed = comparison_checks(base, frame, registration)
    assert all(checks.values()) and all(fits.values()) and changed == [3]
    assert observed["packet_count_delta"] == 1 and observed["sound4_payload_bytes"] == 46
    assert records[0]["after_raw_header"]["bytes_after_header"] == 37


@pytest.mark.capture
def test_unexpected_owner_is_a_hypothesis_failure_not_a_checksum_repair_target(key2_capture):
    base, registration = key2_capture[1], key2_capture[3]
    checks, fits, _, _, _ = comparison_checks(base, with_sound4(base, owner=0), registration)
    assert all(checks.values()) and not fits["sound4_record_is_self_owned_buffer"]


@pytest.mark.capture
def test_global_allocation_bookkeeping_can_be_reported_without_invalidating_pattern_preservation(
    key2_capture,
):
    base, registration = key2_capture[1], key2_capture[3]
    packets = list(with_sound4(base).packets)
    payload = bytearray(packets[1].payload)
    payload[20] ^= 1
    packets[1] = Packet(packets[1].tag, bytes(payload))
    checks, fits, _, _, observed = comparison_checks(base, reframed(packets), registration)
    assert all(checks.values()) and fits["all_other_sound_records_unchanged"]
    assert (
        not fits["only_sound4_data_packets_added"]
        and not observed["non_sound4_plain_packet_sequence_unchanged"]
    )


@pytest.mark.capture
def test_possible_existing_buffer_relocation_is_reported_independently(key2_capture):
    base, registration = key2_capture[1], key2_capture[3]
    packets = list(with_sound4(base).packets)
    payload = bytearray(packets[111].payload)
    payload[20] ^= 1
    packets[111] = Packet(packets[111].tag, bytes(payload))
    checks, fits, changed, _, _ = comparison_checks(base, reframed(packets), registration)
    assert all(checks.values()) and changed == [0, 3]
    assert (
        not fits["existing_owner0_header_and_codes_unchanged"]
        and not fits["all_other_sound_records_unchanged"]
    )


@pytest.mark.capture
def test_pattern_changes_or_no_new_sound_do_not_pass_allocation_control(key2_capture):
    base, registration = key2_capture[1], key2_capture[3]
    allocated = with_sound4(base)
    data = bytearray(pattern_data(allocated, 1))
    data[905] = 16
    checks, _, _, _, _ = comparison_checks(
        base, reframed(_replace_pattern_data(allocated, 1, bytes(data))), registration
    )
    assert checks["all_native_checksums"] and not checks["all_patterns_unchanged"]
    checks, _, _, _, _ = comparison_checks(base, base, registration)
    assert not checks["target_sound4_data_present"]


@pytest.mark.capture
def test_project_projects_key2_without_guessing_its_sample_selector_or_preview(
    key2_capture, tmp_path
):
    _, actual, _, _, capture, artifact = key2_capture
    output = tmp_path / "project"
    report = export_project(
        artifact, capture, output, calibrated_windows=True, calibrated_drum_slices=True
    )
    events = json.loads((output / "patterns/01.json").read_text())["observed_cells"]
    assert [
        (e["step"], e["calibrated_drum_slice_key"])
        for e in events
        if e["candidate_sound_slot"] == 10
    ] == [(1, 1), (9, 2)]
    sounds = json.loads((output / "sounds.json").read_text())["sounds"]
    assert "keyboard_key" not in sounds[9]["slice_records"][1]
    assert sounds[9]["preview_slice_keys"] == [1]
    assert (
        packets_from_view(json.loads((output / "source/packets.json").read_text()))
        == actual.packets
    )
    for name, record in report["files"].items():
        assert sha256_file(output / name) == record["sha256"]
