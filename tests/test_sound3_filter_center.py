"""Center scalar hypotheses and prior-component comparison must remain separable."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_center import center_report
from scripts.sound3_filter_center_audio import compare_center_audio


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-filter-A-center-registration-001.json"
    if not path.exists():
        pytest.skip("Registered FILTER center required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


def synthetic_center(base, values):
    data = bytearray(pattern_data(base, 1))
    for step, value in enumerate(values):
        p = 48 * step + 6
        data[p + 1] = (data[p + 1] & 15) | ((value & 15) << 4)
        data[p + 2] = (data[p + 2] & 252) | (value >> 4)
    return decode_frame(bytes(4095) + encode_packets(_replace_pattern_data(base, 1, bytes(data))))


@pytest.mark.capture
def test_actual_endpoints_and_frozen_prior_audio_are_pinned_before_new_center(states):
    root, _, registration = states
    observation_path = (
        root
        / "experiments/event-057-d-return-sound3-filter-A-lock-up/hardware-observation-001.json"
    )
    observation = json.loads(observation_path.read_text())
    assert observation["hardware_verified"] and all(observation["checks"].values())
    assert sha256_file(observation_path) == registration["source_observation_sha256"]
    assert registration["expected_interior_raw_code"] is None
    assert registration["reference_audio_already_observed"]
    assert (
        sha256_file(root / registration["reference_audio_results"])
        == registration["reference_audio_results_sha256"]
    )


@pytest.mark.capture
@pytest.mark.parametrize(
    "value,contiguous,alternate",
    [(31, True, False), (32, True, False), (33, True, True), (63, False, False)],
)
def test_scalar_order_checks_are_separate_and_do_not_force_a_center_code(
    states, value, contiguous, alternate
):
    _, base, registration = states
    report = center_report(base, synthetic_center(base, [value] * 16), registration)
    assert (
        report["actual_native_controls_pass"]
        and report["strict_candidate_mask_and_all_other_state_preserved"]
    )
    assert (
        report["monotonic_scalar_order_checks"]["all_contiguous_values_between_endpoints"]
        is contiguous
    )
    assert (
        report["monotonic_scalar_order_checks"]["all_alternative_values_between_endpoints"]
        is alternate
    )
    assert report["raw_contiguous_values"] == [value] * 16
    assert not report["filter_general_model_or_units_confirmed"]


@pytest.mark.capture
def test_mixed_center_values_stay_literal_and_hidden_volume_change_fails_scope(states):
    _, base, registration = states
    values = [31, 32] * 8
    center = synthetic_center(base, values)
    report = center_report(base, center, registration)
    assert report["raw_contiguous_values"] == values and not report["values_uniform"]
    data = bytearray(pattern_data(center, 1))
    data[6] ^= 64
    bad = decode_frame(bytes(4095) + encode_packets(_replace_pattern_data(center, 1, bytes(data))))
    report = center_report(base, bad, registration)
    assert not report["strict_candidate_mask_and_all_other_state_preserved"]
    assert not report["pitch14_and_volume36_preserved"]


def audio_summary(registration, amplitude):
    parameters = registration["frequency_method"]["parameters"]
    measurements = [
        {
            "threshold_peak_fraction": fraction,
            "median_frequency_hz": 530.2515,
            "loop_median_seconds": 2.4,
            "usable": True,
            "fits": [{"fundamental_amplitude": amplitude}] * 7,
        }
        for fraction in parameters["threshold_peak_fractions"]
    ]
    return {
        "parameters": parameters,
        "passed": True,
        "channels": {
            name: {"measurements": copy.deepcopy(measurements)} for name in ("left", "right")
        },
    }


def test_near_prior_amplitude_requires_frequency_loop_and_all_six_consistent_comparisons(states):
    registration = states[2]
    prior = audio_summary(registration, 0.05)
    near = compare_center_audio(prior, audio_summary(registration, 0.049), registration)
    reduced = compare_center_audio(prior, audio_summary(registration, 0.035), registration)
    assert near["all_near_reference_amplitudes_supported"] and near["comparison_usable"]
    assert reduced["comparison_usable"] and not reduced["all_near_reference_amplitudes_supported"]
    assert (
        not near["broadband_bypass_or_filter_law_confirmed"] and not near["filter_writer_enabled"]
    )


@pytest.mark.parametrize("damage", ["frequency", "loop", "failed", "one_channel"])
def test_inconsistent_prior_component_or_failed_audio_cannot_pass_neutral_hypothesis(
    states, damage
):
    registration = states[2]
    prior = audio_summary(registration, 0.05)
    center = audio_summary(registration, 0.05)
    if damage == "failed":
        center["passed"] = False
    else:
        for item in center["channels"]["right"]["measurements"]:
            if damage == "frequency":
                item["median_frequency_hz"] = 550
            elif damage == "loop":
                item["loop_median_seconds"] = 2.5
            else:
                item["fits"] = [{"fundamental_amplitude": 0.03}] * 7
    report = compare_center_audio(prior, center, registration)
    assert not report["all_near_reference_amplitudes_supported"]


def test_changed_method_rejected_and_unusable_thresholds_retained_as_failed_comparison(states):
    registration = states[2]
    prior = audio_summary(registration, 0.05)
    center = audio_summary(registration, 0.05)
    center["channels"]["left"]["measurements"].pop()
    assert not compare_center_audio(prior, center, registration)["comparison_usable"]
    center = copy.deepcopy(audio_summary(registration, 0.05))
    center["parameters"]["center_frequency_hz"] = 530
    with pytest.raises(ValueError, match="frozen center"):
        compare_center_audio(prior, center, registration)
