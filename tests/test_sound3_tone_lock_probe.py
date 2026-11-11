"""Keep actual live-volume no-change evidence and classify opaque recorded cells strictly."""

import hashlib
import json
from pathlib import Path

import pytest

from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_tone_lock_probe import probe_checks
from scripts.check_sound3_volume_probe import probe_checks as live_checks


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/event-042-b-sound3-tone-volume-minimum"
    if not (folder / "hardware-observation-001.json").exists():
        pytest.skip("Completed live-volume control required")
    observation = json.loads((folder / "hardware-observation-001.json").read_text())
    assert (
        observation["hardware_verified"] and observation["audition_result"] == "quieter_not_silent"
    )
    base = decode_artifact(load_artifact(root / observation["artifact_path"]))
    registration = json.loads(
        (root / "experiments/sound3-tone-lock-probe-registration-001.json").read_text()
    )
    return root, base, registration


def altered(frame, packet_index, offsets):
    packets = list(frame.packets)
    data = bytearray(packets[packet_index].payload)
    for offset, value in offsets.items():
        data[offset] = value
    packets[packet_index] = Packet(packets[packet_index].tag, bytes(data))
    return decode_frame(bytes(4095) + encode_packets(packets))


def pattern_change(frame, offset, value):
    return altered(frame, 4 + offset // 255, {offset % 255: value})


@pytest.mark.capture
def test_actual_selection_and_live_volume_backups_are_complete_equal_states(states):
    root, minimum, _ = states
    path = root / "experiments/sound3-tone-volume-probe-registration-001.json"
    registration = json.loads(path.read_text())
    baseline = decode_artifact(load_artifact(root / registration["baseline_artifact"]))
    selection = decode_artifact(
        load_artifact(
            root
            / "experiments/event-041-a-sound3-tone-selected/derived/analysis-001/capture.symbols.npz"
        )
    )
    report = live_checks(baseline, selection, minimum, registration)
    assert (
        report["control_passed"] and report["musical_state_preserved_except_unknown_live_parameter"]
    )
    assert report["location_hypotheses"]["selection_only_no_serialized_change"]
    assert report["location_hypotheses"]["volume_no_serialized_change"]
    assert baseline.packets == selection.packets == minimum.packets


@pytest.mark.capture
def test_sound3_primary_changes_are_observed_without_inventing_volume_bitfields(states):
    _, base, registration = states
    locked = pattern_change(base, 55, 0x55)
    report = probe_checks(base, base, locked, registration)
    assert report["location_hypotheses"]["tone_lock_only_pattern1_sound3_primary_cells_changed"]
    assert (
        report["pattern1_changed_cells_against_actual_playbackA"][0]["primary_after_hex"]
        == "0d5583"
    )
    assert not report["volume_specific_bitfield_confirmed"] and not report["volume_writer_enabled"]


@pytest.mark.capture
def test_changed_auxiliary_values_are_not_hidden_in_primary_only_hypothesis(states):
    _, base, registration = states
    locked = pattern_change(base, 786, 0xF6)
    report = probe_checks(base, base, locked, registration)
    assert not report["location_hypotheses"]["tone_lock_only_pattern1_sound3_primary_cells_changed"]
    assert report["location_hypotheses"][
        "tone_lock_only_pattern1_sound3_primary_and_auxiliary_cells_changed"
    ]
    assert report["pattern1_changed_cells_against_actual_playbackA"][0]["auxiliary_before"] == 0xFF


@pytest.mark.capture
def test_previously_empty_sound3_cells_remain_visible_without_claiming_added_notes(states):
    _, base, registration = states
    locked = pattern_change(base, 48 * 2 + 6, 0x22)
    report = probe_checks(base, base, locked, registration)
    cell = report["pattern1_changed_cells_against_actual_playbackA"][0]
    assert (
        cell["step"] == 3 and cell["sound_slot"] == 3 and cell["previously_completely_empty_cell"]
    )
    assert not report["pitch_field_writer_enabled"]


@pytest.mark.capture
@pytest.mark.parametrize("offset", [51, 1024])
def test_other_sound_or_footer_change_refutes_selected_sound_locality(states, offset):
    _, base, registration = states
    locked = pattern_change(base, offset, 0x22)
    report = probe_checks(base, base, locked, registration)
    assert not report["location_hypotheses"][
        "tone_lock_only_pattern1_sound3_primary_and_auxiliary_cells_changed"
    ]
    assert report["lock_raw_changes_against_actual_playbackA"]


@pytest.mark.capture
def test_actual_playbackA_is_the_lock_baseline_even_if_it_changed_another_field(states):
    _, base, registration = states
    playback = altered(base, 2, {50: 7})
    locked = pattern_change(playback, 55, 0x55)
    report = probe_checks(base, playback, locked, registration)
    assert not report["plain_playback_body_matches_preregistered_prediction"]
    assert report["plain_playback_raw_changes_against_prior_baseline"]
    assert report["lock_preservation_checks"]["all_non_pattern_packets_unchanged"]
    assert report["location_hypotheses"]["tone_lock_only_pattern1_sound3_primary_cells_changed"]


@pytest.mark.capture
def test_ineffective_lock_and_wrong_source_remain_explicit_results(states):
    _, base, registration = states
    report = probe_checks(base, base, base, registration)
    assert report["location_hypotheses"]["tone_lock_no_serialized_change"]
    assert not report["location_hypotheses"]["tone_lock_only_pattern1_sound3_primary_cells_changed"]
    wrong = dict(registration, baseline_body_sha256=hashlib.sha256(b"wrong").hexdigest())
    assert not probe_checks(base, base, base, wrong)["control_passed"]
