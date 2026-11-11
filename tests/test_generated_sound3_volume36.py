"""Reciprocal ordering, exact preservation and independently bound physical evidence."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_sound3_volume18_restore import restore_checks
from scripts.check_generated_sound3_volume36 import evaluate_gain
from scripts.prepare_generated_sound3_volume36 import candidate_packets


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-generated-volume36-registration-002.json"
    if not path.exists():
        pytest.skip("Reciprocal fixed36 control required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


@pytest.mark.capture
def test_reciprocal_target_redecodes_with_only_registered_masks_changed(states):
    root, source, registration = states
    folder = root / "experiments/edited-sound3-volume36-002"
    constructed = decode_frame(bytes(4095) + encode_packets(candidate_packets(source)))
    target, recovered = [
        decode_artifact(load_artifact(folder / name))
        for name in ("edited.symbols.npz", "redecoded.symbols.npz")
    ]
    assert constructed.encoded_body == target.encoded_body
    leg = registration["expected_capture_sequence"][1]
    assert leg["contiguous_raw_code"] == 36 and leg["alternative_order_raw_code"] == 9
    assert all(restore_checks(source, target, recovered, leg, registration).values())
    before, after = pattern_data(source, 1), pattern_data(target, 1)
    for step in range(16):
        p = 48 * step + 6
        assert ((after[p] >> 6) | ((after[p + 1] & 15) << 2)) == 36
        assert (((after[p] >> 6) << 4) | (after[p + 1] & 15)) == 9
        assert (before[p] & 63, before[p + 1] & 240, before[p + 2]) == (
            after[p] & 63,
            after[p + 1] & 240,
            after[p + 2],
        )
    assert leg["contiguous_raw_code"] > 21 > leg["alternative_order_raw_code"]
    report = json.loads((folder / "software-validation.json").read_text())
    assert report["passed"] and not report["hardware_verified"]
    metadata = load_artifact(folder / "edited.symbols.npz").metadata
    assert metadata["transformations"][-1]["alternative_order_raw_code"] == 9
    assert registration["reference_already_observed"]
    assert registration["selected_after_original_volume18_result"]


@pytest.mark.capture
def test_exact_source_guard_and_auxiliary_preservation_reject_unrelated_state(states):
    root, source, registration = states
    other = decode_artifact(
        load_artifact(
            root / "experiments/edited-sound3-volume18-001/derived/analysis-001/capture.symbols.npz"
        )
    )
    with pytest.raises(ValueError, match="Exact independently"):
        candidate_packets(other)
    target = decode_frame(bytes(4095) + encode_packets(candidate_packets(source)))
    packets = list(target.packets)
    data = bytearray(packets[7].payload)
    assert data[786 - 3 * 255] == 0xFF
    data[786 - 3 * 255] = 0xF6
    packets[7] = Packet(packets[7].tag, bytes(data))
    bad = decode_frame(bytes(4095) + encode_packets(packets))
    assert not all(
        restore_checks(
            source, target, bad, registration["expected_capture_sequence"][1], registration
        ).values()
    )


@pytest.fixture(scope="module")
def method():
    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (root / "experiments/sound3-volume18-gain-method-registration-001.json").read_text()
    )


def summary(method, amplitude):
    measurements = [
        {
            "threshold_peak_fraction": fraction,
            "median_amplitude": amplitude,
            "median_frequency_hz": 500.65,
            "loop_median_seconds": 2.4,
            "usable": True,
        }
        for fraction in method["parameters"]["threshold_peak_fractions"]
    ]
    return {
        "parameters": method["parameters"],
        "passed": True,
        "channels": {
            name: {"measurements": copy.deepcopy(measurements)} for name in ("left", "right")
        },
    }


def test_reciprocal_comparison_supports_increase_and_preserves_uncertain_outcomes(method):
    reference = summary(method, 0.06)
    louder = evaluate_gain(reference, summary(method, 0.09), method)
    quieter = evaluate_gain(reference, summary(method, 0.05), method)
    same = evaluate_gain(reference, reference, method)
    assert louder["all_contiguous36_gain_directions_supported"]
    assert not louder["all_alternative9_gain_directions_supported"]
    assert not quieter["all_contiguous36_gain_directions_supported"]
    assert quieter["all_alternative9_gain_directions_supported"]
    assert not same["all_contiguous36_gain_directions_supported"]
    assert not same["all_alternative9_gain_directions_supported"]
    assert not louder["hardware_verified"] and not louder["volume_writer_enabled"]


@pytest.mark.parametrize("change", ["pitch", "loop", "failed", "opposite_channel"])
def test_bad_or_conflicting_measurements_cannot_support_reciprocal_direction(method, change):
    reference = summary(method, 0.06)
    candidate = summary(method, 0.09)
    if change == "failed":
        candidate["passed"] = False
    else:
        for item in candidate["channels"]["right"]["measurements"]:
            key, value = {
                "pitch": ("median_frequency_hz", 550),
                "loop": ("loop_median_seconds", 2.5),
                "opposite_channel": ("median_amplitude", 0.05),
            }[change]
            item[key] = value
    result = evaluate_gain(reference, candidate, method)
    assert not result["all_contiguous36_gain_directions_supported"]
    assert not result["all_alternative9_gain_directions_supported"]


@pytest.mark.capture
def test_completed_volume18_evidence_does_not_invent_subjective_confirmation(states):
    root, _, registration = states
    folder = root / "experiments/edited-sound3-volume18-001"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    manual_path = folder / "manual-observation.json"
    manual = json.loads(manual_path.read_text())
    gain_path = root / "experiments/sound3-generated-volume18-gain-results-001.json"
    gain = json.loads(gain_path.read_text())
    assert sha256_file(observation_path) == registration["prior_generated18_observation_sha256"]
    assert (
        sha256_file(gain_path)
        == observation["gain_results_sha256"]
        == registration["prior_generated18_gain_results_sha256"]
    )
    assert sha256_file(manual_path) == observation["manual_observation_sha256"]
    assert manual["tentative_guess"] == "louder" and not manual["relative_loudness_confirmed"]
    assert not observation["subjective_gain_direction_confirmed"]
    assert observation["hardware_verified"] and all(observation["checks"].values())
    assert gain["all_contiguous_order_gain_directions_supported"]
    assert all(row["amplitude_ratio_candidate_to_reference"] < 0.97 for row in gain["measurements"])
    assert not gain["hardware_verified"]
