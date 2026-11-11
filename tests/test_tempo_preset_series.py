"""Test third-value and return hypotheses against independent known states and alternatives."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo_preset_series import series_checks
from scripts.prepare_tempo_preset_series import predict_preset


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/tempo-preset-series-registration-001.json"
    if not path.exists():
        pytest.skip("Preregistered third-value/return control required")
    reg = json.loads(path.read_text())
    base = decode_artifact(load_artifact(root / reg["baseline_artifact"]))
    original = decode_artifact(load_artifact(root / reg["original120_artifact"]))
    first, returned = predict_preset(base, 80), predict_preset(base, 120)
    return base, first, returned, original, reg


@pytest.mark.capture
def test_fixed_candidate_return_prediction_recovers_whole_independent_genuine120_state(states):
    base, first, returned, original, reg = states
    assert returned.encoded_body == original.encoded_body
    report = series_checks(base, first, returned, original, reg, 80, 120)
    assert report["control_passed"] and report["series_supported"]
    assert all(report["series_hypotheses"].values())


@pytest.mark.capture
def test_genuine_third_preset_and_return_match_every_preregistered_hypothesis(states):
    base, _, _, original, reg = states
    root = Path(__file__).resolve().parents[1]
    first_dir = root / "experiments/event-031-b-tempo-80"
    return_dir = root / "experiments/event-032-a-return-tempo-120"
    first_path = first_dir / "derived/analysis-001/capture.symbols.npz"
    return_path = return_dir / "derived/analysis-001/capture.symbols.npz"
    if not first_path.exists() or not return_path.exists():
        pytest.skip("Actual third-preset and return captures required")
    assert (
        sha256_file(first_dir / "capture.wav")
        == "b83a3a086a6c5eef5c365d98b1032d08fe67d29b65afb200f490b27b170cbfcd"
    )
    assert (
        sha256_file(return_dir / "capture.wav")
        == "80023150ef49d531f72b8b62aad151831a9353b328016751d2388e99fb22e890"
    )
    first, returned = [decode_artifact(load_artifact(path)) for path in (first_path, return_path)]
    report = series_checks(base, first, returned, original, reg, 80, 120)
    assert report["control_passed"] and report["series_supported"]
    assert all(report["series_hypotheses"].values())


@pytest.mark.capture
def test_missing_display_values_do_not_turn_predictions_into_supported_observations(states):
    base, first, returned, original, reg = states
    report = series_checks(base, first, returned, original, reg)
    assert report["control_passed"] and not report["series_supported"]
    assert report["series_hypotheses"]["actual_first_display_matches_registered80"] is None
    assert report["series_hypotheses"]["actual_return_display_matches_registered120"] is None


@pytest.mark.capture
def test_return_candidate_match_does_not_hide_other_global_changes(states):
    base, first, returned, original, reg = states
    packets = list(returned.packets)
    index = next(i for i, p in enumerate(packets) if p.tag == 0x7D5C)
    data = bytearray(packets[index].payload)
    data[0] ^= 1
    packets[index] = Packet(0x7D5C, bytes(data))
    report = series_checks(base, first, native(packets), original, reg, 80, 120)
    assert report["control_passed"] and not report["series_supported"]
    assert report["return_hypotheses"]["candidate_matches_observed_after_BPM"]
    assert not report["series_hypotheses"]["entire_return_body_equals_independent_original120"]
    assert not report["return_hypotheses"]["first_global_record_unchanged"]


@pytest.mark.capture
def test_stale_first_capture_does_not_pass_third_value_even_with_exact_original_return(states):
    base, _, returned, original, reg = states
    report = series_checks(base, base, returned, original, reg, 80, 120)
    assert report["control_passed"] and not report["series_supported"]
    assert report["series_hypotheses"]["entire_return_body_equals_independent_original120"]
    assert not report["series_hypotheses"]["first_body_equals_preregistered80_prediction"]
    assert not report["first_hypotheses"]["candidate_matches_observed_after_BPM"]


@pytest.mark.capture
@pytest.mark.parametrize("value", [True, 140, 81, "80"])
def test_research_predictor_stays_within_the_registered_two_presets(states, value):
    with pytest.raises(ValueError, match="preset predictions"):
        predict_preset(states[0], value)
