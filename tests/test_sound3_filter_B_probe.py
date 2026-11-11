"""FILTER B alternatives retain bit7, ramps, coupled snapshots and no-change results."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.filters import set_calibrated_sound3_filter
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_B_probe import B_probe_report


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-filter-B-minimum-registration-001.json"
    if not path.exists():
        pytest.skip("Registered FILTER B probe required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


def synthesize(base, values, mask=124):
    data = bytearray(pattern_data(base, 1))
    for step, value in enumerate(values):
        p = 48 * step + 8
        data[p] = (data[p] & (255 ^ mask)) | ((value << 2) & mask)
    return decode_frame(bytes(4095) + encode_packets(_replace_pattern_data(base, 1, bytes(data))))


@pytest.mark.capture
def test_exact_generated_center_and_user_confirmation_are_pinned_before_B_data(states):
    root, base, registration = states
    folder = root / "experiments/edited-sound3-filter63-center-001"
    observation = json.loads((folder / "hardware-observation-001.json").read_text())
    manual = json.loads((folder / "manual-observation.json").read_text())
    assert observation["hardware_verified"] and all(observation["checks"].values())
    assert (
        sha256_file(folder / "hardware-observation-001.json")
        == registration["source_observation_sha256"]
    )
    assert manual["user_report"] == "done, and confirmed the sample sounds unfiltered"
    assert registration["registered_before_B_minimum_capture"]
    assert registration["expected_B_endpoint_code"] is None
    assert set_calibrated_sound3_filter(base, 63) == base.packets


@pytest.mark.capture
def test_narrow_and_wide_masks_remain_distinct_and_bit7_not_given_a_role(states):
    _, base, registration = states
    narrow = B_probe_report(base, synthesize(base, [11] * 16), registration)
    wide = B_probe_report(base, synthesize(base, [47] * 16, 252), registration)
    for name in ("third_primary_bits2_to6", "third_primary_bits2_to7"):
        assert narrow["B_candidate_mask_reports"][name]["changed_only_within_candidate_supported"]
    assert narrow["after_projection_uniformity"]["third_bits2_to6_values"]
    assert not narrow["after_projection_uniformity"]["third_bits2_to7_values"]
    assert not wide["B_candidate_mask_reports"]["third_primary_bits2_to6"][
        "changed_only_within_candidate_supported"
    ]
    assert wide["B_candidate_mask_reports"]["third_primary_bits2_to7"][
        "changed_only_within_candidate_supported"
    ]
    assert wide["after_projection_uniformity"]["third_bits2_to7_values"]
    assert not wide["resonance_field_width_scale_or_bit7_role_confirmed"]


@pytest.mark.capture
def test_no_change_is_valid_native_evidence_without_location_support(states):
    _, base, registration = states
    report = B_probe_report(base, base, registration)
    assert report["actual_native_controls_pass"] and report["no_serialized_change"]
    assert all(
        item["only_candidate_bits_and_all_other_state_preserved"]
        for item in report["B_candidate_mask_reports"].values()
    )
    assert not any(
        item["changed_only_within_candidate_supported"]
        for item in report["B_candidate_mask_reports"].values()
    )


@pytest.mark.capture
def test_nonuniform_ramp_is_retained_and_new_B_context_is_not_publicly_accepted(states):
    _, base, registration = states
    actual = synthesize(base, list(range(16)))
    report = B_probe_report(base, actual, registration)
    assert report["raw_B_candidate_projections"]["after"]["third_bits2_to6_values"] == list(
        range(16)
    )
    assert not report["after_projection_uniformity"]["third_bits2_to6_values"]
    assert report["pitch14_and_volume36_preserved"] and report["filter_A63_preserved"]
    with pytest.raises(ValueError, match="Unknown Sound3 filter context"):
        set_calibrated_sound3_filter(actual, 16)


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 8, 770, 3, 1024])
def test_hidden_or_coupled_changes_do_not_widen_strict_masks(states, offset):
    _, base, registration = states
    changed = synthesize(base, [11] * 16)
    data = bytearray(pattern_data(changed, 1))
    data[offset] ^= 16 if offset == 7 else 1
    actual = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(changed, 1, bytes(data)))
    )
    report = B_probe_report(base, actual, registration)
    assert report["actual_native_controls_pass"]
    assert not any(
        item["changed_only_within_candidate_supported"]
        for item in report["B_candidate_mask_reports"].values()
    )
    if offset in (7, 8):
        assert report["broader_FILTER_snapshot_supported"]
        assert not report["filter_A63_preserved"]
    if offset == 770:
        assert report["Sound3_primary_and_auxiliary_changes_supported"]
        assert not report["other_Sound3_primary_changes_supported"]


@pytest.mark.capture
def test_changed_preregistered_mask_rejected_and_stale_source_hash_retained(states):
    _, base, registration = states
    bad = copy.deepcopy(registration)
    bad["B_candidate_masks"]["third_primary_bits2_to7"] = 255
    with pytest.raises(ValueError, match="fixed preregistered"):
        B_probe_report(base, base, bad)
    bad = copy.deepcopy(registration)
    bad["source_body_sha256"] = "0" * 64
    assert not B_probe_report(base, base, bad)["source_body_matches_registration"]
