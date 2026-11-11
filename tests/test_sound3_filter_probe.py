"""FILTER masks stay distinct and actual selection controls anchor the recorded pass."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.formats.pitch import set_calibrated_sound3_pitch
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_probe import recorded_report, selection_report


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def baseline():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-filter-selection-and-A-registration-001.json"
    if not path.exists():
        pytest.skip("Registered FILTER control required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


def changed_filter(base):
    data = bytearray(pattern_data(base, 1))
    for step, value in ((0, 44), (2, 10), (8, 21)):
        p = 48 * step + 6
        data[p + 1] = (data[p + 1] & 15) | ((value & 15) << 4)
        data[p + 2] = (data[p + 2] & 252) | (value >> 4)
    return data


@pytest.mark.capture
def test_genuine_generated14_frequency_result_is_bound_before_filter_data(baseline):
    root, _, registration = baseline
    folder = root / "experiments/edited-sound3-pitch14-001"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    result_path = root / "experiments/sound3-generated-pitch13-14-frequency-results-001.json"
    result = json.loads(result_path.read_text())
    assert observation["hardware_verified"] and all(observation["checks"].values())
    assert sha256_file(observation_path) == registration["source_observation_sha256"]
    assert sha256_file(result_path) == observation["interval_results_sha256"]
    assert result["all_one_semitone_ratios_supported"] and not result["hardware_verified"]
    assert registration["registered_before_both_captures"]


@pytest.mark.capture
def test_no_change_remains_an_alternative_and_selection_prediction_is_exact(baseline):
    _, source, registration = baseline
    assert all(selection_report(source, source, registration).values())
    report = recorded_report(source, source, registration)
    assert report["location_hypotheses"]["no_serialized_change"]
    assert not any(
        v for k, v in report["location_hypotheses"].items() if k != "no_serialized_change"
    )
    assert not report["filter_writer_enabled"]


@pytest.mark.capture
def test_strict_candidate_retains_mixed_values_and_leaves_pitch_volume_literal(baseline):
    _, source, registration = baseline
    actual = native(_replace_pattern_data(source, 1, bytes(changed_filter(source))))
    report = recorded_report(source, actual, registration)
    assert (
        all(report["native_checks"].values())
        and report["location_hypotheses"]["strict_candidate_mask_only"]
    )
    assert report["candidate_changed_steps"] == [1, 3, 9]
    assert report["raw_Sound3_fields"]["after"]["volume_values"] == [36] * 16
    assert report["raw_Sound3_fields"]["after"]["first_low5_values"] == [14] * 16
    assert report["raw_Sound3_fields"]["after"]["uninterpreted_candidate_values"][2] == 10
    assert not report["uniform_endpoint_required"]
    with pytest.raises(ValueError, match="Unknown Sound3 pitch context"):
        set_calibrated_sound3_pitch(actual, 13)


@pytest.mark.capture
def test_coupled_third_byte_is_not_silently_called_strict_candidate(baseline):
    _, source, registration = baseline
    data = changed_filter(source)
    data[8] ^= 4
    report = recorded_report(
        source, native(_replace_pattern_data(source, 1, bytes(data))), registration
    )
    assert not report["location_hypotheses"]["strict_candidate_mask_only"]
    assert report["location_hypotheses"]["candidate_plus_other_third_byte_bits"]
    assert report["raw_Sound3_fields"]["after"]["uninterpreted_third_high6_values"][0] == 33


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 770])
def test_pitch_volume_or_auxiliary_changes_remain_broader_outcomes(baseline, offset):
    _, source, registration = baseline
    data = changed_filter(source)
    data[offset] ^= 1
    report = recorded_report(
        source, native(_replace_pattern_data(source, 1, bytes(data))), registration
    )
    assert not report["location_hypotheses"]["strict_candidate_mask_only"]
    assert not report["location_hypotheses"]["candidate_plus_other_third_byte_bits"]
    assert report["location_hypotheses"]["Sound3_primary_and_auxiliary_changes"]


@pytest.mark.capture
@pytest.mark.parametrize("damage", ["neighbor", "footer", "other_pattern", "sample"])
def test_changes_outside_sound3_pattern1_reject_scoped_hypotheses(baseline, damage):
    _, source, registration = baseline
    data = changed_filter(source)
    if damage in ("neighbor", "footer"):
        data[3 if damage == "neighbor" else 1024] ^= 1
    actual = native(_replace_pattern_data(source, 1, bytes(data)))
    if damage == "other_pattern":
        other = bytearray(pattern_data(actual, 2))
        other[0] ^= 1
        actual = native(_replace_pattern_data(actual, 2, bytes(other)))
    elif damage == "sample":
        packets = list(actual.packets)
        index = next(i for i, p in enumerate(packets) if p.tag == 0xEF78 and len(p.payload) == 255)
        payload = bytearray(packets[index].payload)
        payload[15] ^= 1
        packets[index] = Packet(packets[index].tag, bytes(payload))
        actual = native(packets)
    report = recorded_report(source, actual, registration)
    assert all(report["native_checks"].values())
    assert not any(report["location_hypotheses"].values())


@pytest.mark.capture
def test_changed_selection_is_not_fitted_to_prediction_and_recorded_pass_uses_actual_A(baseline):
    _, source, registration = baseline
    packets = list(source.packets)
    payload = bytearray(packets[2].payload)
    payload[131] ^= 1
    packets[2] = Packet(packets[2].tag, bytes(payload))
    selected = native(packets)
    selection = selection_report(source, selected, registration)
    assert not selection["entire_selection_body_matches_prediction"]
    assert selection["source_body_matches_registration"] and selection["expected_native_geometry"]
    recorded = native(_replace_pattern_data(selected, 1, bytes(changed_filter(selected))))
    report = recorded_report(selected, recorded, registration)
    assert (
        report["actual_A_body_sha256_used_as_B_source"]
        == hashlib.sha256(selected.encoded_body).hexdigest()
    )
    assert report["location_hypotheses"]["strict_candidate_mask_only"]


@pytest.mark.capture
def test_changed_registered_masks_are_rejected(baseline):
    _, source, registration = baseline
    changed = copy.deepcopy(registration)
    changed["candidate"]["third_primary_mask"] = 255
    with pytest.raises(ValueError, match="fixed preregistered"):
        recorded_report(source, source, changed)
