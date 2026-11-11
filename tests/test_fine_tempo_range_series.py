"""Verify the real fine100 control and distinguish missing readings and incomplete returns."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.globals import calibrated_tempo_preset, set_calibrated_tempo_preset
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.modem.symbols import load_artifact
from scripts.check_fine_tempo_range_series import range_series_checks
from scripts.check_tempo_control import comparison_checks
from scripts.prepare_fine_tempo_range_series import predict_range_frames


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/event-033-b-fine-tempo-100"
    path = folder / "derived/analysis-001/capture.symbols.npz"
    if not path.exists():
        pytest.skip("Actual physical fine100 control required")
    assert (
        sha256_file(folder / "capture.wav")
        == "a296fe64000e078997becbc2b9acba5a2a986b6172168658e0cfbe874859ea1b"
    )
    assert sha256_file(path) == "b802ea9c8306d5c048ecd95fc629f8c3546a097f1765931b3a49544e96698280"
    fine100 = decode_artifact(load_artifact(path))
    original_reg = json.loads((folder / "tempo-registration.json").read_text())
    before80 = decode_artifact(load_artifact(root / original_reg["baseline_artifact"]))
    reg = json.loads(
        (root / "experiments/fine-tempo-range-series-registration-001.json").read_text()
    )
    predictions = predict_range_frames(fine100)
    return fine100, before80, original_reg, reg, predictions


@pytest.mark.capture
def test_real_fine100_changes_only_registered_byte_and_preserves_all_other_state(states):
    actual, before, reg, _, _ = states
    controls, fits, observed = comparison_checks(before, actual, reg, 80, 100)
    assert all(controls.values()) and all(fits.values())
    assert observed["candidate_changed_offsets"] == [129]
    assert observed["candidate_after"] == 100
    assert observed["changed_packets"][0]["before_tag"] == "0x7d5c"


@pytest.mark.capture
def test_endpoint_models_and_return_pass_fixed_predictions_only_as_software_evidence(states):
    original, _, _, reg, predicted = states
    report = range_series_checks(original, predicted, reg, [60, 240, 100])
    assert report["control_passed"] and report["series_supported"]
    assert all(report["return_hypotheses"].values())
    assert predicted[-1].encoded_body == original.encoded_body


@pytest.mark.capture
def test_actual_fine_endpoints_and_return_match_all_preregistered_hypotheses(states):
    original, _, _, reg, _ = states
    root = Path(__file__).resolve().parents[1]
    identities = json.loads(
        (root / "experiments/fine-tempo-range-series-results-001.json").read_text()
    )["captures"]
    frames = []
    for expected, identity in zip(reg["expected_capture_sequence"], identities):
        folder = root / "experiments" / expected["experiment_id"]
        assert sha256_file(folder / "capture.wav") == identity["capture_sha256"]
        path = Path(identity["artifact_path"])
        assert sha256_file(path) == identity["artifact_sha256"]
        frames.append(decode_artifact(load_artifact(path)))
    report = range_series_checks(original, frames, reg, [60, 240, 100])
    assert report["control_passed"] and report["series_supported"]
    assert all(report["return_hypotheses"].values())


@pytest.mark.capture
def test_candidate_values_do_not_supply_missing_display_observations(states):
    original, _, _, reg, predicted = states
    report = range_series_checks(original, predicted, reg)
    assert report["control_passed"] and not report["series_supported"]
    assert all(
        leg["prediction_hypotheses"]["actual_display_matches_requested_value"] is None
        for leg in report["legs"]
    )


@pytest.mark.capture
def test_changed_global_byte_on_return_fails_even_with_correct100_candidate(states):
    original, _, _, reg, predictions = states
    packets = list(predictions[-1].packets)
    data = bytearray(packets[1].payload)
    data[0] ^= 1
    packets[1] = Packet(0x7D5C, bytes(data))
    changed = (*predictions[:2], native(packets))
    report = range_series_checks(original, changed, reg, [60, 240, 100])
    assert report["control_passed"] and not report["series_supported"]
    assert report["legs"][-1]["tempo_hypothesis_checks"]["candidate_matches_observed_after_BPM"]
    assert not report["return_hypotheses"]["entire_return_body_equals_independent_original100"]


@pytest.mark.capture
def test_stale_minimum_capture_cannot_be_hidden_by_correct_maximum_and_return(states):
    original, _, _, reg, predictions = states
    report = range_series_checks(original, (original, *predictions[1:]), reg, [60, 240, 100])
    assert report["control_passed"] and not report["series_supported"]
    assert all(report["return_hypotheses"].values())
    assert not report["legs"][0]["prediction_hypotheses"]["body_matches_preregistered_prediction"]


@pytest.mark.capture
def test_sample_corruption_with_valid_checksums_fails_core_isolation(states):
    original, _, _, reg, predictions = states
    packets = list(predictions[1].packets)
    index = sound_groups(predictions[1])[0][1]
    data = bytearray(packets[index].payload)
    data[23] ^= 1
    packets[index] = Packet(0xEF78, bytes(data))
    report = range_series_checks(
        original, (predictions[0], native(packets), predictions[2]), reg, [60, 240, 100]
    )
    assert not report["control_passed"] and not report["series_supported"]
    assert not report["legs"][1]["control_checks"]["all_sample_records_unchanged"]


@pytest.mark.capture
@pytest.mark.parametrize("readings", [[60, 240], [60, 240, 100, 120]])
def test_incomplete_or_extra_display_sequence_is_not_silently_truncated(states, readings):
    original, _, _, reg, predictions = states
    with pytest.raises(ValueError, match="Exactly three"):
        range_series_checks(original, predictions, reg, readings)


@pytest.mark.capture
def test_missing_capture_is_not_treated_as_a_complete_series(states):
    original, _, _, reg, predictions = states
    with pytest.raises(ValueError, match="Exactly three"):
        range_series_checks(original, predictions[:2], reg, [60, 240, 100])


@pytest.mark.capture
def test_research_predictor_rejects_foreign_source_and_presets_do_not_expand(states):
    original, before80, _, _, predictions = states
    with pytest.raises(ValueError, match="fine100 state"):
        predict_range_frames(before80)
    for frame in (original, *predictions):
        with pytest.raises(ValueError, match="Source tempo"):
            calibrated_tempo_preset(frame)
    for bpm in (60, 100, 240):
        with pytest.raises(ValueError, match="Tempo preset"):
            set_calibrated_tempo_preset(before80, bpm)
