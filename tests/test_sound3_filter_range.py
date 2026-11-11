"""Opposite FILTER data stays unknown and exact return requires every byte."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.formats.pitch import set_calibrated_sound3_pitch
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_range import range_report


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-filter-A-range-registration-001.json"
    if not path.exists():
        pytest.skip("FILTER range registration required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


def synthetic_opposite(base, values):
    data = bytearray(pattern_data(base, 1))
    for step, value in enumerate(values):
        p = 48 * step + 6
        data[p + 1] = (data[p + 1] & 15) | ((value & 15) << 4)
        data[p + 2] = (data[p + 2] & 252) | (value >> 4)
    return native(_replace_pattern_data(base, 1, bytes(data)))


@pytest.mark.capture
def test_genuine_clockwise62_retains_qualitative_inaudibility_and_unchanged_state(states):
    root, source, registration = states
    folder = root / "experiments/event-055-b-sound3-filter-A-lock-up"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    manual = json.loads((folder / "manual-observation.json").read_text())
    model = json.loads((folder / "clockwise-post-observation-model-001.json").read_text())
    assert observation["hardware_verified"] and all(observation["checks"].values())
    assert sha256_file(observation_path) == registration["source_observation_sha256"]
    assert observation["contiguous_candidate_values"] == [62] * 16
    assert observation["alternative_candidate_values"] == [59] * 16
    assert manual["audible_endpoint"] == "sample_no_longer_audible_to_user"
    assert manual["numeric_display_value"] is None and not observation["digital_silence_measured"]
    assert not model["registered_before_clockwise_data"] and model["complete_body_reproduced"]
    with pytest.raises(ValueError, match="Unknown Sound3 pitch context"):
        set_calibrated_sound3_pitch(source, 13)


@pytest.mark.capture
@pytest.mark.parametrize("values", [[7] * 16, [16] * 16, list(range(2, 18))])
def test_independent_opposite_values_and_ramps_remain_literal_with_both_projections(states, values):
    _, source, registration = states
    opposite = synthetic_opposite(source, values)
    report = range_report(source, opposite, source, registration)
    assert report["source_body_matches_registration"] and report["both_actual_native_controls_pass"]
    assert (
        report["strict_candidate_mask_preserved_in_both_legs"]
        and report["pitch14_and_volume36_preserved"]
    )
    assert report["contiguous_values_by_leg"][0] == values
    assert report["alternative_values_by_leg"][0] == [
        ((value & 15) << 2) | (value >> 4) for value in values
    ]
    assert report["counterclockwise_values_uniform"] is (len(set(values)) == 1)
    assert report["all_exact_return_checks_pass"]
    assert registration["expected_capture_sequence"][0]["expected_endpoint_code"] is None
    assert (
        not report["filter_bit_order_width_or_Hz_scale_confirmed"]
        and not report["filter_writer_enabled"]
    )


@pytest.mark.capture
def test_no_opposite_change_is_visible_even_if_return_is_exact(states):
    _, source, registration = states
    report = range_report(source, source, source, registration)
    assert (
        not report["counterclockwise_candidate_changes"] and report["all_exact_return_checks_pass"]
    )


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 8, 770, 3, 1024])
def test_matching_candidate_values_cannot_rescue_hidden_return_changes(states, offset):
    _, source, registration = states
    data = bytearray(pattern_data(source, 1))
    data[offset] ^= 1
    returned = native(_replace_pattern_data(source, 1, bytes(data)))
    report = range_report(source, synthetic_opposite(source, [7] * 16), returned, registration)
    assert report["both_actual_native_controls_pass"]
    assert not report["all_exact_return_checks_pass"]
    assert not report["exact_return_checks"][
        "entire_return_body_and_packets_equal_independent_clockwise"
    ]


@pytest.mark.capture
def test_coupled_third_bits_remain_broader_without_widening_the_strict_mask(states):
    _, source, registration = states
    opposite = synthetic_opposite(source, [7] * 16)
    data = bytearray(pattern_data(opposite, 1))
    data[8] ^= 4
    opposite = native(_replace_pattern_data(opposite, 1, bytes(data)))
    report = range_report(source, opposite, source, registration)
    assert not report["strict_candidate_mask_preserved_in_both_legs"]
    assert report["location_reports_against_registered_clockwise"][0]["location_hypotheses"][
        "candidate_plus_other_third_byte_bits"
    ]


@pytest.mark.capture
def test_stale_source_body_hash_cannot_be_called_a_valid_range_control(states):
    _, source, registration = states
    stale = copy.deepcopy(registration)
    stale["source_body_sha256"] = "0" * 64
    report = range_report(source, synthetic_opposite(source, [7] * 16), source, stale)
    assert not report["source_body_matches_registration"]
