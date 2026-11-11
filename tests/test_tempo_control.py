"""Distinguish tempo candidates, absent storage and unrelated changes without byte fitting."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo_control import comparison_checks


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def source():
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments/event-030-b-tempo-preset-once/tempo-registration.json"
    if not registration_path.exists():
        pytest.skip("Registered tempo control required")
    registration = json.loads(registration_path.read_text())
    path = root / registration["baseline_artifact"]
    assert sha256_file(path) == registration["baseline_artifact_sha256"]
    before = decode_artifact(load_artifact(path))
    return before, registration


def alter_global(before, offsets, occurrence=1):
    packets = list(before.packets)
    index = [i for i, p in enumerate(packets) if p.tag == 0x7D5C][occurrence]
    data = bytearray(packets[index].payload)
    for offset, value in offsets.items():
        data[offset] = value
    packets[index] = Packet(0x7D5C, bytes(data))
    return native(packets)


@pytest.mark.capture
def test_known_transition_supports_registered_candidate_but_is_only_synthetic_evidence(source):
    before, reg = source
    controls, fits, observed = comparison_checks(
        before, alter_global(before, {129: 140}), reg, 120, 140
    )
    assert all(controls.values()) and all(fits.values())
    assert observed["single_byte_hypothesis_status"] == "supported_for_this_transition"
    assert observed["changed_packets"][0]["changed_payload_bytes"] == [
        {"offset_zero_based": 129, "before": 120, "after": 140}
    ]


@pytest.mark.capture
def test_genuine_120_to140_capture_changes_only_the_preregistered_byte(source):
    before, reg = source
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-030-b-tempo-preset-once"
    path = directory / "derived/analysis-001/capture.symbols.npz"
    if not path.exists():
        pytest.skip("Actual first tempo control required")
    assert (
        sha256_file(directory / "capture.wav")
        == "cedcdd9b97674b93b3ebb623e3ebd2744ddb4f188a9fd899eac9407903efc1ef"
    )
    assert sha256_file(path) == "b6d4e617213811f5bdcfabe389172989bda3d30eaf3a38923adcc0bde1891690"
    actual = decode_artifact(load_artifact(path))
    controls, fits, observed = comparison_checks(before, actual, reg, 120, 140)
    assert all(controls.values()) and all(fits.values())
    assert observed["changed_packets"] == [
        {
            "packet_index_zero_based": 2,
            "before_tag": "0x7d5c",
            "after_tag": "0x7d5c",
            "before_payload_bytes": 255,
            "after_payload_bytes": 255,
            "changed_payload_bytes": [{"offset_zero_based": 129, "before": 120, "after": 140}],
        }
    ]


@pytest.mark.capture
def test_candidate_bytes_are_not_used_as_substitutes_for_missing_display_observations(source):
    before, reg = source
    _, fits, observed = comparison_checks(before, alter_global(before, {129: 140}), reg)
    assert fits["baseline_candidate_matches_observed_before_BPM"] is None
    assert fits["candidate_matches_observed_after_BPM"] is None
    assert observed["single_byte_hypothesis_status"] == "not_evaluated_without_display_observations"


@pytest.mark.capture
def test_identical_dump_is_valid_no_serialized_change_outcome(source):
    before, reg = source
    controls, fits, observed = comparison_checks(before, before, reg, 120, 140)
    assert all(controls.values())
    assert not fits["native_body_changed"] and not fits["only_registered_candidate_byte_changed"]
    assert observed["single_byte_hypothesis_status"] == "not_supported_for_this_transition"


@pytest.mark.capture
@pytest.mark.parametrize("offsets", [{130: 140}, {129: 140, 130: 1}])
def test_wrong_offset_or_extra_byte_is_reported_without_refitting_the_hypothesis(source, offsets):
    before, reg = source
    controls, fits, observed = comparison_checks(
        before, alter_global(before, offsets), reg, 120, 140
    )
    assert all(controls.values()) and not fits["only_registered_candidate_byte_changed"]
    assert observed["candidate_changed_offsets"] == sorted(offsets)
    assert observed["single_byte_hypothesis_status"] == "not_supported_for_this_transition"


@pytest.mark.capture
def test_wrong_observed_display_rejects_numeric_coincidence(source):
    before, reg = source
    _, fits, observed = comparison_checks(before, alter_global(before, {129: 140}), reg, 80, 120)
    assert not fits["baseline_candidate_matches_observed_before_BPM"]
    assert not fits["candidate_matches_observed_after_BPM"]
    assert observed["single_byte_hypothesis_status"] == "not_supported_for_this_transition"


@pytest.mark.capture
def test_first_global_change_is_visible_even_when_candidate_matches_display(source):
    before, reg = source
    candidate = alter_global(before, {129: 140})
    changed = alter_global(candidate, {0: 0}, occurrence=0)
    controls, fits, observed = comparison_checks(before, changed, reg, 120, 140)
    assert all(controls.values()) and not fits["first_global_record_unchanged"]
    assert len(observed["changed_packets"]) == 2
    assert observed["single_byte_hypothesis_status"] == "not_supported_for_this_transition"


@pytest.mark.capture
def test_sample_corruption_with_valid_checksums_fails_isolation_controls(source):
    before, reg = source
    packets = list(before.packets)
    index = sound_groups(before)[0][1]
    raw = bytearray(packets[index].payload)
    raw[20] ^= 1
    packets[index] = Packet(0xEF78, bytes(raw))
    controls, fits, observed = comparison_checks(before, native(packets), reg, 120, 140)
    assert not controls["all_sample_records_unchanged"]
    assert not fits["all_non_global_packets_unchanged"]
    assert observed["changed_packets"][0]["before_tag"] == "0xef78"


@pytest.mark.capture
@pytest.mark.parametrize("value", [True, 59, 241, "120"])
def test_display_observations_require_actual_integer_BPM(source, value):
    before, reg = source
    with pytest.raises(ValueError, match="Observed display BPM"):
        comparison_checks(before, before, reg, value, 140)
