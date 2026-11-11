"""Preserve the observed TONE model and falsifiable low-nibble minimum prediction."""

import json
from pathlib import Path

import pytest

from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_tone_lock_probe import probe_checks
from scripts.check_sound3_volume_lock_range import range_checks
from scripts.prepare_sound3_volume_lock_range import minimum_prediction_packets


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    observation_path = (
        root / "experiments/event-044-b-sound3-tone-volume-lock-up/hardware-observation-001.json"
    )
    if not observation_path.exists():
        pytest.skip("Recorded Sound3 TONE endpoint required")
    observation = json.loads(observation_path.read_text())
    assert observation["hardware_verified"] and observation["audition_result"] == "louder"
    maximum = decode_artifact(load_artifact(root / observation["artifact_path"]))
    baseline = decode_artifact(
        load_artifact(
            root
            / "experiments/event-043-a-sound3-plain-playback/derived/analysis-001/capture.symbols.npz"
        )
    )
    initial = json.loads(
        (root / "experiments/sound3-tone-lock-probe-registration-001.json").read_text()
    )
    registration = json.loads(
        (root / "experiments/sound3-volume-lock-range-registration-001.json").read_text()
    )
    return root, baseline, maximum, initial, registration


@pytest.mark.capture
def test_actual_recorded_tone_changes_all16_primary_cells_and_no_auxiliary_or_other_state(states):
    _, baseline, maximum, initial, _ = states
    report = probe_checks(baseline, baseline, maximum, initial)
    assert report["control_passed"] and all(report["lock_preservation_checks"].values())
    assert report["location_hypotheses"]["tone_lock_only_pattern1_sound3_primary_cells_changed"]
    assert len(report["pattern1_changed_cells_against_actual_playbackA"]) == 16
    before, after = pattern_data(baseline, 1), pattern_data(maximum, 1)
    model = bytearray(before)
    for step in range(16):
        model[48 * step + 6] |= 0xC0
        model[48 * step + 7] = (model[48 * step + 7] & 0xF0) | 15
    assert after == bytes(model)
    assert not report["volume_specific_bitfield_confirmed"]


@pytest.mark.capture
def test_minimum_prediction_and_return_preserve_all_bits_outside_registered_low_nibbles(states):
    root, _, maximum, _, reg = states
    predicted = native(minimum_prediction_packets(maximum))
    assert (
        predicted.encoded_body
        == (
            root
            / "experiments/event-045-c-sound3-tone-volume-lock-minimum/predicted-native-body.bin"
        ).read_bytes()
    )
    report = range_checks(maximum, predicted, maximum, reg)
    assert report["low_nibble_minimum_and_exact_return_supported"]
    assert report["actual_minimum_raw_nibbles"] == [0] * 16
    assert (
        not report["numeric_display_values_inferred"]
        and not report["gain_scale_or_mute_behavior_confirmed"]
    )
    assert not report["volume_writer_enabled"]


@pytest.mark.capture
def test_another_minimum_value_is_reported_as_failed_prediction_without_refitting(states):
    _, _, maximum, _, reg = states
    data = bytearray(pattern_data(maximum, 1))
    for step in range(16):
        data[48 * step + 7] = (data[48 * step + 7] & 0xF0) | 1
    observed = native(_replace_pattern_data(maximum, 1, bytes(data)))
    report = range_checks(maximum, observed, maximum, reg)
    assert report["control_passed"] and all(report["minimum_preservation_checks"].values())
    assert report["actual_minimum_raw_nibbles"] == [1] * 16
    assert not report["hypothesis_checks"]["minimum_all16_raw_nibbles_zero"]
    assert not report["low_nibble_minimum_and_exact_return_supported"]


@pytest.mark.capture
def test_high_flag_or_auxiliary_change_cannot_be_hidden_in_candidate_mask(states):
    _, _, maximum, _, reg = states
    minimum = native(minimum_prediction_packets(maximum))
    for offset in (6, 786):
        data = bytearray(pattern_data(minimum, 1))
        data[offset] ^= 0x40
        observed = native(_replace_pattern_data(minimum, 1, bytes(data)))
        report = range_checks(maximum, observed, maximum, reg)
        assert not report["minimum_preservation_checks"][
            "all_pattern1_bits_except_candidate_low_nibbles_unchanged"
        ]
        assert not report["low_nibble_minimum_and_exact_return_supported"]


@pytest.mark.capture
def test_correct_return_nibbles_with_another_global_change_fail_entire_return(states):
    _, _, maximum, _, reg = states
    packets = list(maximum.packets)
    data = bytearray(packets[2].payload)
    data[131] = 1
    packets[2] = Packet(0x7D5C, bytes(data))
    report = range_checks(
        maximum, native(minimum_prediction_packets(maximum)), native(packets), reg
    )
    assert report["hypothesis_checks"]["return_all16_raw_nibbles_f"]
    assert not report["hypothesis_checks"][
        "complete_return_body_equals_independent_original_maximum"
    ]
    assert not report["low_nibble_minimum_and_exact_return_supported"]


@pytest.mark.capture
def test_research_prediction_rejects_other_source_and_moved_candidate(states):
    _, baseline, maximum, _, reg = states
    with pytest.raises(ValueError, match="Exact independently"):
        minimum_prediction_packets(baseline)
    moved = dict(
        reg,
        candidate=dict(
            reg["candidate"],
            concatenated_pattern_payload_offsets_zero_based=[48 * step + 8 for step in range(16)],
        ),
    )
    with pytest.raises(ValueError, match="preregistered16"):
        range_checks(maximum, maximum, maximum, moved)
