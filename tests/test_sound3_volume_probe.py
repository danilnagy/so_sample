"""Keep selection and volume hypotheses independent and retain unexpected raw changes."""

import hashlib
from pathlib import Path

import pytest

from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_volume_probe import probe_checks


@pytest.fixture(scope="module")
def baseline():
    path = (
        Path(__file__).resolve().parents[1]
        / "experiments/edited-joint-tempo100-swing9-001/derived/analysis-001/capture.symbols.npz"
    )
    if not path.exists():
        pytest.skip("Accepted joint100/swing9 capture required")
    frame = decode_artifact(load_artifact(path))
    registration = {
        "baseline_body_sha256": hashlib.sha256(frame.encoded_body).hexdigest(),
        "expected_tempo_bpm": 100,
        "expected_swing_byte": 9,
    }
    return frame, registration


def changed(frame, index, offset, value):
    packets = list(frame.packets)
    data = bytearray(packets[index].payload)
    data[offset] = value
    packets[index] = Packet(packets[index].tag, bytes(data))
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.mark.capture
def test_unchanged_live_setting_remains_a_valid_explicit_hypothesis(baseline):
    base, reg = baseline
    report = probe_checks(base, base, base, reg)
    assert (
        report["control_passed"] and report["musical_state_preserved_except_unknown_live_parameter"]
    )
    assert report["location_hypotheses"]["volume_no_serialized_change"]
    assert not report["volume_writer_enabled"] and not report["minimum_display_value_inferred"]


@pytest.mark.capture
def test_volume_is_compared_against_actual_selectionA_not_original_sound8(baseline):
    base, reg = baseline
    selection = changed(base, 2, 50, 7)
    report = probe_checks(base, selection, selection, reg)
    assert report["selection_changes_against_original_baseline"]
    assert report["minimum_changes_against_actual_selectionA"] == []
    assert not report["location_hypotheses"]["selection_only_no_serialized_change"]
    assert report["location_hypotheses"]["volume_no_serialized_change"]


@pytest.mark.capture
def test_new_global_field_is_reported_raw_without_assuming_volume_location_or_scale(baseline):
    base, reg = baseline
    minimum = changed(base, 2, 51, 11)
    report = probe_checks(base, base, minimum, reg)
    assert report["musical_state_preserved_except_unknown_live_parameter"]
    assert report["location_hypotheses"]["volume_changes_only_global_packets"]
    assert report["minimum_changes_against_actual_selectionA"][0]["changed_payload_bytes"] == [
        {"offset_zero_based": 51, "before": 0, "after": 11}
    ]
    assert not report["minimum_display_value_inferred"]


@pytest.mark.capture
def test_unexpected_pattern_or_sample_changes_are_retained_and_fail_preservation(baseline):
    base, reg = baseline
    pattern = changed(base, 4, 54, 99)
    report = probe_checks(base, base, pattern, reg)
    assert (
        report["control_passed"]
        and not report["musical_state_preserved_except_unknown_live_parameter"]
    )
    assert report["location_hypotheses"]["volume_changes_pattern_data"]
    index = sound_groups(base)[0][1]
    sample = changed(base, index, 20, base.packets[index].payload[20] ^ 1)
    report = probe_checks(base, base, sample, reg)
    assert report["location_hypotheses"]["volume_changes_sample_records"]
    assert not report["minimum_preservation_checks"]["all_sample_records_and_codes_unchanged"]


@pytest.mark.capture
def test_tempo_change_or_wrong_source_identity_does_not_pass_control_scope(baseline):
    base, reg = baseline
    other = changed(base, 2, 129, 101)
    assert not probe_checks(base, base, other, reg)["minimum_preservation_checks"][
        "tempo100_and_swing9_preserved"
    ]
    report = probe_checks(other, other, other, reg)
    assert not report["control_passed"]
