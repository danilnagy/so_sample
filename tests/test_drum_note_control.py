"""Test drum-note preservation separately from still-unobserved encoding predictions."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_note_control import comparison_checks


@pytest.fixture(scope="module")
def drum_note_baseline():
    root = Path(__file__).resolve().parents[1]
    registration = json.loads((root / "experiments/drum10-note-predictions-001.json").read_text())
    directory = root / "experiments/event-020-b-drum10-key1-step1"
    artifact = directory / registration["baseline_artifact"]
    if not artifact.exists():
        pytest.skip("Genuine accepted cross-drum copy baseline required")
    assert sha256_file(artifact) == registration["baseline_artifact_sha256"]
    return decode_artifact(load_artifact(artifact)), registration


def with_note(frame, slot=10, primary=b"\x01\x02\x03", auxiliary=0xF0):
    data = bytearray(pattern_data(frame, 1))
    p, a = 3 * (slot - 1), 768 + slot - 1
    data[p : p + 3], data[a] = primary, auxiliary
    return decode_frame(bytes(4095) + encode_packets(_replace_pattern_data(frame, 1, bytes(data))))


@pytest.mark.capture
def test_unknown_drum_primary_can_pass_preservation_without_matching_either_melodic_prediction(
    drum_note_baseline,
):
    base, registration = drum_note_baseline
    checks, fits, packets, _, observed = comparison_checks(base, with_note(base), registration)
    assert all(checks.values()) and packets == [4, 7]
    assert fits["sound10_maps_to_cell10"] and fits["auxiliary_key1_matches_melodic_F0"]
    assert not fits["primary_matches_sound2_key1"] and not fits["primary_matches_sound3_key1"]
    assert observed["candidate_primary_hex"] == "010203"


@pytest.mark.capture
def test_unchanged_zero_auxiliary_remains_a_prediction_failure_without_invalidating_locality(
    drum_note_baseline,
):
    base, registration = drum_note_baseline
    checks, fits, packets, _, _ = comparison_checks(
        base, with_note(base, auxiliary=0), registration
    )
    assert all(checks.values()) and packets == [4]
    assert fits["sound10_maps_to_cell10"]
    assert (
        not fits["auxiliary_key1_matches_melodic_F0"] and not fits["changed_plain_packet_indices"]
    )


@pytest.mark.capture
def test_different_empty_sound_cell_fails_sound10_mapping_independently(drum_note_baseline):
    base, registration = drum_note_baseline
    checks, fits, _, _, observed = comparison_checks(base, with_note(base, slot=2), registration)
    assert all(checks.values()) and observed["changed_raw_sound_cells"] == [2]
    assert not fits["sound10_maps_to_cell10"]


@pytest.mark.capture
@pytest.mark.parametrize(
    "damage", ["existing_neighbor", "other_step", "footer", "source_sample", "second_new_cell"]
)
def test_checksum_valid_unrelated_changes_fail_drum_note_control(drum_note_baseline, damage):
    base, registration = drum_note_baseline
    note = with_note(base)
    if damage == "source_sample":
        packets = list(note.packets)
        payload = bytearray(packets[111].payload)
        payload[20] ^= 1
        packets[111] = Packet(packets[111].tag, bytes(payload))
        altered = decode_frame(bytes(4095) + encode_packets(packets))
    else:
        data = bytearray(pattern_data(note, 1))
        offset = {"existing_neighbor": 6, "other_step": 48, "footer": 1024, "second_new_cell": 3}[
            damage
        ]
        data[offset] ^= 1
        altered = decode_frame(
            bytes(4095) + encode_packets(_replace_pattern_data(note, 1, bytes(data)))
        )
    checks, _, _, _, _ = comparison_checks(base, altered, registration)
    assert checks["all_native_checksums"] and not all(checks.values())


@pytest.mark.capture
def test_no_added_note_does_not_pass_control(drum_note_baseline):
    base, registration = drum_note_baseline
    checks, _, packets, _, _ = comparison_checks(base, base, registration)
    assert packets == [] and not checks["one_previously_empty_raw_step1_cell_changed"]
