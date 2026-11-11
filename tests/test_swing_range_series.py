"""Preserve fixed swing hypotheses and separate unsigned/signed minimum models."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.globals import set_calibrated_tempo
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.symbols import load_artifact
from scripts.check_swing_max_control import comparison_checks
from scripts.check_swing_range_series import series_checks


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


def swing_value(frame, value):
    packets = list(frame.packets)
    old = packets[2].payload
    packets[2] = Packet(0x7D5C, old[:130] + bytes([value & 255]) + old[131:])
    return native(packets)


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/event-037-b-swing-maximum"
    if not (folder / "hardware-observation-001.json").exists():
        pytest.skip("Observed swing maximumS18 required")
    observation = json.loads((folder / "hardware-observation-001.json").read_text())
    assert (
        sha256_file(folder / "capture.wav")
        == "2fd1195678408838c33a89488f0a9b131c143c9a962f3a9964d22ef70d290339"
    )
    path = root / observation["artifact_path"]
    assert sha256_file(path) == observation["artifact_sha256"]
    maximum = decode_artifact(load_artifact(path))
    reg = json.loads((root / "experiments/swing-range-series-registration-001.json").read_text())
    zero = decode_artifact(load_artifact(root / reg["original_zero_artifact"]))
    first_reg = json.loads((folder / "swing-registration.json").read_text())
    return maximum, zero, reg, first_reg


@pytest.mark.capture
def test_actual_S18_changes_only_registered_location_and_preserves_tempo137(states):
    maximum, zero, _, first_reg = states
    controls, fits, observed = comparison_checks(zero, maximum, first_reg, 18, "S18")
    assert all(controls.values()) and all(fits.values())
    assert observed["candidate_changed_offsets"] == [130] and observed["candidate_after"] == 18
    assert not observed["numeric_swing_encoding_confirmed"]


@pytest.mark.capture
def test_unsigned_minimum_zero_model_recovers_complete_independent_original_state(states):
    maximum, zero, reg, _ = states
    frames = (swing_value(maximum, 0), swing_value(maximum, 9), maximum)
    report = series_checks(maximum, frames, zero, reg, [0, 9, 18])
    assert report["control_passed"] and report["series_supported"]
    assert report["encoding_models"]["direct_unsigned_supported_across_all_values"]
    assert report["return_hypotheses"]["minimum0_complete_body_equals_original_zero_state"]


@pytest.mark.capture
def test_signed_negative_minimum_remains_an_independent_preregistered_alternative(states):
    maximum, zero, reg, _ = states
    frames = (swing_value(maximum, -18), swing_value(maximum, 9), maximum)
    report = series_checks(maximum, frames, zero, reg, [-18, 9, 18])
    assert report["control_passed"] and report["series_supported"]
    assert not report["encoding_models"]["direct_unsigned_supported_across_all_values"]
    assert report["encoding_models"]["direct_signed_supported_across_all_values"]
    assert report["return_hypotheses"]["minimum0_complete_body_equals_original_zero_state"] is None


@pytest.mark.capture
def test_display_readings_are_not_inferred_from_raw_candidate_values(states):
    maximum, zero, reg, _ = states
    report = series_checks(maximum, (zero, swing_value(maximum, 9), maximum), zero, reg)
    assert report["control_passed"] and not report["series_supported"]
    assert all(value is None for value in report["encoding_models"].values())


@pytest.mark.capture
def test_wrong_display_or_scale_does_not_refit_the_encoded_values(states):
    maximum, zero, reg, _ = states
    report = series_checks(
        maximum, (zero, swing_value(maximum, 9), maximum), zero, reg, [0, 50, 100]
    )
    assert report["control_passed"] and not report["series_supported"]
    assert not any(report["encoding_models"].values())


@pytest.mark.capture
def test_correct_return_swing_value_does_not_hide_another_changed_global_byte(states):
    maximum, zero, reg, _ = states
    packets = list(maximum.packets)
    data = bytearray(packets[1].payload)
    data[0] ^= 1
    packets[1] = Packet(0x7D5C, bytes(data))
    report = series_checks(
        maximum, (zero, swing_value(maximum, 9), native(packets)), zero, reg, [0, 9, 18]
    )
    assert report["control_passed"] and not report["series_supported"]
    assert not report["return_hypotheses"]["complete_return_body_equals_originalS18"]


@pytest.mark.capture
def test_observed_swing_context_is_not_silently_reset_by_tempo_edit(states):
    edited = native(set_calibrated_tempo(states[0], 120))
    assert edited.packets[2].payload[129:131] == bytes([120, 18])
    assert edited.packets[2].payload[:129] == states[0].packets[2].payload[:129]
    assert edited.packets[2].payload[130:] == states[0].packets[2].payload[130:]


@pytest.mark.capture
def test_missing_capture_or_display_sequence_is_not_silently_truncated(states):
    maximum, zero, reg, _ = states
    with pytest.raises(ValueError, match="Exactly three"):
        series_checks(maximum, (zero, maximum), zero, reg, [0, 9, 18])
    with pytest.raises(ValueError, match="Exactly three"):
        series_checks(maximum, (zero, swing_value(maximum, 9), maximum), zero, reg, [0, 9])
