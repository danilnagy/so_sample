"""Unknown B maxima and complete minimum returns retain failures and context guards."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.filters import set_calibrated_sound3_filter
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_B_range import B_range_report


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-filter-B-range-registration-001.json"
    if not path.exists():
        pytest.skip("Registered B range required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


def synthetic_B(base, values):
    data = bytearray(pattern_data(base, 1))
    for step, value in enumerate(values):
        data[48 * step + 8] = (data[48 * step + 8] & 3) | (value << 2)
    return decode_frame(bytes(4095) + encode_packets(_replace_pattern_data(base, 1, bytes(data))))


@pytest.mark.capture
def test_genuine_minimum_zero_narrow_failure_and_public_context_guard_are_pinned(states):
    root, base, registration = states
    folder = root / "experiments/event-062-a-sound3-filter-B-lock-down"
    observation = json.loads((folder / "hardware-observation-001.json").read_text())
    report = json.loads((folder / "B-probe-results-001.json").read_text())
    model = json.loads(
        (root / "experiments/sound3-filter-B-minimum-post-observation-model-001.json").read_text()
    )
    assert (
        sha256_file(folder / "hardware-observation-001.json")
        == registration["source_observation_sha256"]
    )
    assert sha256_file(folder / "B-probe-results-001.json") == registration["source_results_sha256"]
    assert observation["hardware_verified"] and all(observation["checks"].values())
    assert report["B_candidate_mask_reports"]["third_primary_bits2_to7"]["changed_steps"] == [
        1,
        2,
        5,
        9,
        13,
    ]
    assert not report["B_candidate_mask_reports"]["third_primary_bits2_to6"][
        "only_candidate_bits_and_all_other_state_preserved"
    ]
    assert report["raw_B_candidate_projections"]["after"]["third_bits2_to7_values"] == [0] * 16
    assert not model["registered_before_B_minimum_data"] and model["complete_body_reproduced"]
    with pytest.raises(ValueError, match="Unknown Sound3 filter context"):
        set_calibrated_sound3_filter(base, 16)


@pytest.mark.capture
@pytest.mark.parametrize("value", [0, 7, 31, 32, 63])
def test_unknown_maximum_values_do_not_need_a_guessed_endpoint_or_narrow_mask_success(
    states, value
):
    _, base, registration = states
    report = B_range_report(base, synthetic_B(base, [value] * 16), base, registration)
    assert report["both_actual_native_controls_pass"]
    assert report["six_bit_mask_and_all_other_state_preserved_both_legs"]
    assert report["pitch14_volume36_and_filter_A63_preserved"]
    assert report["six_bit_values_by_leg"] == [[value] * 16, [0] * 16]
    assert report["five_bit_values_by_leg"] == [[value & 31] * 16, [0] * 16]
    assert report["maximum_candidate_changed"] is (value != 0)
    assert report["all_exact_minimum_return_checks_pass"]
    assert registration["expected_capture_sequence"][0]["expected_endpoint_code"] is None
    assert not report["resonance_writer_enabled"]


@pytest.mark.capture
def test_ramp_is_literal_and_never_averaged(states):
    _, base, registration = states
    values = list(range(16))
    report = B_range_report(base, synthetic_B(base, values), base, registration)
    assert report["six_bit_values_by_leg"][0] == values
    assert not report["location_reports_against_independent_minimum"][0][
        "after_projection_uniformity"
    ]["third_bits2_to7_values"]


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 8, 770, 3, 1024])
def test_zero_B_fields_cannot_rescue_hidden_return_changes(states, offset):
    _, base, registration = states
    data = bytearray(pattern_data(base, 1))
    data[offset] ^= 1
    returned = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(base, 1, bytes(data)))
    )
    report = B_range_report(base, synthetic_B(base, [31] * 16), returned, registration)
    assert report["both_actual_native_controls_pass"]
    assert report["exact_return_checks"]["all16_six_bit_return_values_match_registered_zero"]
    assert not report["all_exact_minimum_return_checks_pass"]
    assert not report["six_bit_mask_and_all_other_state_preserved_both_legs"]


@pytest.mark.capture
def test_coupled_A_change_is_broader_without_strict_mask_rescue(states):
    _, base, registration = states
    maximum = synthetic_B(base, [31] * 16)
    data = bytearray(pattern_data(maximum, 1))
    data[7] ^= 16
    coupled = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(maximum, 1, bytes(data)))
    )
    report = B_range_report(base, coupled, base, registration)
    assert report["location_reports_against_independent_minimum"][0][
        "broader_FILTER_snapshot_supported"
    ]
    assert not report["six_bit_mask_and_all_other_state_preserved_both_legs"]
    assert not report["pitch14_volume36_and_filter_A63_preserved"]


@pytest.mark.capture
def test_stale_minimum_body_and_return_prediction_do_not_pass(states):
    _, base, registration = states
    stale = copy.deepcopy(registration)
    stale["source_body_sha256"] = "0" * 64
    assert not B_range_report(base, base, base, stale)["source_body_matches_registration"]
    stale = copy.deepcopy(registration)
    stale["expected_capture_sequence"][1]["expected_complete_body_sha256"] = "0" * 64
    assert not B_range_report(base, base, base, stale)["all_exact_minimum_return_checks_pass"]
