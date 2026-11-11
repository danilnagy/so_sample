"""Range controls must preserve unknowns, separate masks and require the whole return."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.formats.volume import set_calibrated_sound3_volume
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_tone_pitch_range import range_report


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-tone-pitch-range-registration-001.json"
    if not path.exists():
        pytest.skip("Pitch range registration required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


def synthetic_upper(base, values):
    data = bytearray(pattern_data(base, 1))
    for step, value in enumerate(values):
        data[48 * step + 6] = (data[48 * step + 6] & 192) | value
    return native(_replace_pattern_data(base, 1, bytes(data)))


@pytest.mark.capture
def test_actual_minimum_supports_strict_location_without_numeric_display_or_width_claim(states):
    root, source, registration = states
    folder = root / "experiments/event-051-b-sound3-tone-pitch-lock-down"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    manual = json.loads((folder / "manual-observation.json").read_text())
    report = json.loads((folder / "pitch-probe-results-001.json").read_text())
    model = json.loads((folder / "minimum-post-observation-model-001.json").read_text())
    assert observation["hardware_verified"] and all(observation["checks"].values())
    assert sha256_file(observation_path) == registration["source_observation_sha256"]
    assert report["location_hypotheses"]["strict_pitch_candidate_only"]
    assert report["raw_sound3_fields"]["after"]["first_primary_low6_values"] == [1] * 16
    assert report["raw_sound3_fields"]["after"]["known_volume_values"] == [36] * 16
    assert manual["audition"] == "lower" and manual["display_label"] == "Ptc"
    assert manual["numeric_display_value"] is None
    assert (
        not observation["pitch_field_width_confirmed"] and not observation["pitch_scale_confirmed"]
    )
    assert not model["registered_before_minimum_data"]
    with pytest.raises(ValueError, match="Unknown Sound3"):
        set_calibrated_sound3_volume(source, 21)


@pytest.mark.capture
@pytest.mark.parametrize(
    "values,narrower", [([20] * 16, True), ([33] * 16, False), (list(range(2, 18)), True)]
)
def test_independent_upper_values_ramps_and_sixth_bit_are_not_fitted_into_one_model(
    states, values, narrower
):
    _, source, registration = states
    maximum = synthetic_upper(source, values)
    report = range_report(source, maximum, source, registration)
    assert report["control_passed"] and report["all_non_target_state_preserved"]
    assert report["mask_hypotheses"]["only_first_low6_bits_changed_in_both_legs"]
    assert report["mask_hypotheses"]["only_first_low5_bits_changed_in_both_legs"] is narrower
    assert report["maximum_first_low6_values_by_step"] == values
    assert report["maximum_values_uniform"] is (len(set(values)) == 1)
    assert report["all_exact_return_checks_pass"] and report["volume36_preserved_in_both_legs"]
    assert registration["expected_capture_sequence"][0]["expected_endpoint_code"] is None
    assert (
        not report["pitch_scale_or_field_width_confirmed"]
        and not report["pitch_field_writer_enabled"]
    )


@pytest.mark.capture
def test_no_upper_change_is_visible_even_with_exact_return(states):
    _, source, registration = states
    report = range_report(source, source, source, registration)
    assert not report["maximum_changes_candidate_bits"]
    assert report["all_exact_return_checks_pass"]
    assert not report["pitch_field_writer_enabled"]


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 8, 770, 3, 1024])
def test_complete_return_is_not_rescued_by_matching_only_some_candidate_values(states, offset):
    _, source, registration = states
    maximum = synthetic_upper(source, [20] * 16)
    data = bytearray(pattern_data(source, 1))
    data[offset] ^= 1
    returned = native(_replace_pattern_data(source, 1, bytes(data)))
    report = range_report(source, maximum, returned, registration)
    assert report["control_passed"]
    assert not report["all_exact_return_checks_pass"]
    assert not report["exact_return_checks"][
        "entire_return_body_and_packets_equal_independent_minimum"
    ]


@pytest.mark.capture
def test_volume_snapshot_fails_strict_mask_but_remains_explicit(states):
    _, source, registration = states
    maximum = synthetic_upper(source, [20] * 16)
    data = bytearray(pattern_data(maximum, 1))
    data[6] ^= 64
    maximum = native(_replace_pattern_data(maximum, 1, bytes(data)))
    report = range_report(source, maximum, source, registration)
    assert report["control_passed"] and report["all_non_target_state_preserved"]
    assert not report["volume36_preserved_in_both_legs"]
    assert not report["mask_hypotheses"]["only_first_low6_bits_changed_in_both_legs"]
    assert report["location_reports_against_registered_minimum"][0]["location_hypotheses"][
        "pitch_candidate_plus_known_volume"
    ]


@pytest.mark.capture
def test_stale_registered_source_hash_fails_native_control(states):
    _, source, registration = states
    wrong = copy.deepcopy(registration)
    wrong["source_body_sha256"] = "0" * 64
    report = range_report(source, synthetic_upper(source, [20] * 16), source, wrong)
    assert not report["control_passed"]
