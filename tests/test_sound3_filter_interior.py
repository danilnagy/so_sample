"""Interior branch hypotheses cannot rescue failed center predictions or hidden changes."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_interior import interior_report


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-filter-A-interior-registration-001.json"
    if not path.exists():
        pytest.skip("Registered FILTER interiors required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


def synthesize(base, values):
    data = bytearray(pattern_data(base, 1))
    for step, value in enumerate(values):
        data[48 * step + 7] = (data[48 * step + 7] & 15) | ((value & 15) << 4)
        data[48 * step + 8] = (data[48 * step + 8] & 252) | (value >> 4)
    return decode_frame(bytes(4095) + encode_packets(_replace_pattern_data(base, 1, bytes(data))))


@pytest.mark.capture
def test_actual_center_failed_orderings_audio_and_display_correction_are_pinned(states):
    root, base, registration = states
    folder = root / "experiments/event-058-e-sound3-filter-A-center"
    native = json.loads((folder / "center-native-results-001.json").read_text())
    observation = json.loads((folder / "hardware-observation-001.json").read_text())
    manual = json.loads((folder / "manual-observation.json").read_text())
    audio = json.loads((folder / "center-audio-comparison-results-001.json").read_text())
    assert (
        sha256_file(folder / "hardware-observation-001.json")
        == registration["source_observation_sha256"]
    )
    assert (
        sha256_file(folder / "center-native-results-001.json")
        == registration["source_native_results_sha256"]
    )
    assert (
        sha256_file(folder / "center-audio-comparison-results-001.json")
        == registration["source_audio_comparison_sha256"]
    )
    assert native["raw_contiguous_values"] == native["raw_alternative_values"] == [63] * 16
    assert not any(native["monotonic_scalar_order_checks"].values())
    assert observation["hardware_verified"] and all(observation["checks"].values())
    assert manual["display_center"] == "single_tick_in_middle"
    assert not manual["prior_full_bar_center_instruction_supported"]
    assert audio["stored_center_and_near_reference_component_supported"]
    assert not audio["broadband_bypass_or_filter_law_confirmed"]
    assert registration["model_revised_after_center63_observation"]
    assert registration["registered_before_all_three_captures"]
    assert [
        leg.get("expected_raw_code") for leg in registration["expected_capture_sequence"][:2]
    ] == [None, None]
    assert interior_report(base, base, base, base, registration)[
        "all_exact_center_return_checks_pass"
    ]


@pytest.mark.capture
@pytest.mark.parametrize(
    "low,high,contiguous,alternative",
    [
        (16, 47, True, False),
        (7, 45, True, True),
        (2, 61, True, True),
        (1, 62, False, False),
        (63, 63, False, False),
        (32, 31, False, False),
        (0, 0, False, False),
    ],
)
def test_branch_orders_are_separate_and_exact_return_does_not_depend_on_their_success(
    states, low, high, contiguous, alternative
):
    _, base, registration = states
    report = interior_report(
        base, synthesize(base, [low] * 16), synthesize(base, [high] * 16), base, registration
    )
    assert report["all_actual_native_controls_pass"]
    assert all(report["strict_candidate_mask_and_all_other_state_preserved_by_leg"])
    assert report["pitch14_and_volume36_preserved"]
    assert report["all_exact_center_return_checks_pass"]
    assert (
        report["branch_scalar_order_checks"]["contiguous"]["both_branch_order_hypotheses_supported"]
        is contiguous
    )
    assert (
        report["branch_scalar_order_checks"]["alternative"][
            "both_branch_order_hypotheses_supported"
        ]
        is alternative
    )
    assert report["contiguous_values_by_leg"] == [[low] * 16, [high] * 16, [63] * 16]
    assert not report["filter_bit_order_width_mode_or_Hz_scale_confirmed"]
    assert not report["filter_writer_enabled"]


@pytest.mark.capture
def test_ramps_and_retained_center_cells_are_not_averaged_or_rescued(states):
    _, base, registration = states
    low = list(range(2, 18))
    high = list(range(32, 48))
    report = interior_report(
        base, synthesize(base, low), synthesize(base, high), base, registration
    )
    assert report["contiguous_values_by_leg"] == [low, high, [63] * 16]
    assert report["values_uniform_by_leg"] == [False, False, True]
    assert report["branch_scalar_order_checks"]["contiguous"][
        "both_branch_order_hypotheses_supported"
    ]
    low[-1] = 63
    report = interior_report(
        base, synthesize(base, low), synthesize(base, high), base, registration
    )
    assert not report["branch_scalar_order_checks"]["contiguous"][
        "both_branch_order_hypotheses_supported"
    ]
    assert report["contiguous_values_by_leg"][0][-1] == 63


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 8, 770, 3, 1024])
def test_matching_center_candidate_cannot_rescue_hidden_return_changes(states, offset):
    _, base, registration = states
    data = bytearray(pattern_data(base, 1))
    data[offset] ^= 4 if offset == 8 else 1
    bad = decode_frame(bytes(4095) + encode_packets(_replace_pattern_data(base, 1, bytes(data))))
    report = interior_report(
        base, synthesize(base, [16] * 16), synthesize(base, [47] * 16), bad, registration
    )
    assert report["all_actual_native_controls_pass"]
    assert report["exact_return_checks"]["all_contiguous_values_match_registered_center"]
    assert not report["all_exact_center_return_checks_pass"]
    assert not report["strict_candidate_mask_and_all_other_state_preserved_by_leg"][2]


@pytest.mark.capture
def test_wider_interior_changes_stay_broader_and_stale_source_pin_fails(states):
    _, base, registration = states
    low = synthesize(base, [16] * 16)
    data = bytearray(pattern_data(low, 1))
    data[8] ^= 4
    wider = decode_frame(bytes(4095) + encode_packets(_replace_pattern_data(low, 1, bytes(data))))
    report = interior_report(base, wider, synthesize(base, [47] * 16), base, registration)
    assert not report["strict_candidate_mask_and_all_other_state_preserved_by_leg"][0]
    assert report["location_reports_against_independent_center"][0]["location_hypotheses"][
        "candidate_plus_other_third_byte_bits"
    ]
    assert not report["branch_scalar_order_checks"]["contiguous"][
        "both_branch_order_hypotheses_supported"
    ]
    stale = copy.deepcopy(registration)
    stale["source_body_sha256"] = "0" * 64
    assert not interior_report(base, low, synthesize(base, [47] * 16), base, stale)[
        "source_body_matches_registration"
    ]
