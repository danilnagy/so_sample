"""New footer/global hypotheses cannot rescue the original strict failure or hidden state."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_pattern1_fx_return_controls import return_report


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/pattern1-FX8-clear-return-registration-001.json"
    if not path.exists():
        pytest.skip("Registered FX8/clear controls required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    baseline_path = root / registration["independent_no_FX_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    assert sha256_file(baseline_path) == registration["independent_no_FX_artifact_sha256"]
    return (
        root,
        decode_artifact(load_artifact(source_path)),
        decode_artifact(load_artifact(baseline_path)),
        registration,
    )


def synthesize(base, footer, global_value):
    data = bytearray(pattern_data(base, 1))
    data[1024:] = footer
    packets = list(_replace_pattern_data(base, 1, bytes(data)))
    payload = bytearray(packets[2].payload)
    payload[131] = global_value
    packets[2] = Packet(packets[2].tag, bytes(payload))
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.mark.capture
def test_original_footer_only_failure_and_post_observation_revision_are_explicit(states):
    root, source, _, registration = states
    folder = root / "experiments/event-065-a-pattern1-FX7-recorded"
    report = json.loads((folder / "FX-probe-results-001.json").read_text())
    model = json.loads(
        (
            root / "experiments/pattern1-FX7-footer-global-post-observation-model-001.json"
        ).read_text()
    )
    assert not report["only_Pattern1_footer_changed_supported"]
    assert not report["preservation_checks"]["all_nonpattern_packets_and_samples_unchanged"]
    assert pattern_data(source, 1)[1024:] == bytes([0x66]) * 8
    assert source.packets[2].payload[131] == 9
    assert not model["registered_before_FX7_data"] and model["complete_body_reproduced"]
    assert registration["scope_revised_after_FX7_observation"]
    assert registration["registered_before_both_captures"]
    assert all(
        leg["expected_global_byte"] is None for leg in registration["expected_capture_sequence"]
    )


@pytest.mark.capture
@pytest.mark.parametrize("global_value", [0, 9, 10, 15, 128, 255])
def test_global_byte_unknown_and_narrow_whole_byte_scopes_are_separate(states, global_value):
    _, source, baseline, registration = states
    down = synthesize(source, bytes([0x77]) * 8, global_value)
    cleared = synthesize(source, bytes([0xFF]) * 8, global_value)
    report = return_report(source, down, cleared, baseline, registration)
    assert report["both_actual_native_controls_pass"]
    assert report["footer_plus_global_whole_byte_scope_by_leg"] == [True, True]
    assert report["footer_plus_global_low4_scope_by_leg"] == [global_value < 16] * 2
    assert report["footer_mapping_prediction_matches_by_leg"] == [True, True]
    assert report["clear_matches_independent_no_FX_except_global131"]
    assert report["clear_entire_body_and_packets_equal_independent_no_FX_diagnostic"] is (
        global_value == 0
    )
    assert not report["FX_writer_enabled"]


@pytest.mark.capture
def test_failed_code_prediction_and_mixed_values_remain_literal(states):
    _, source, baseline, registration = states
    mixed = bytes([0x76, 0x77, 0x77, 0x77, 0x77, 0x77, 0x77, 0xFF])
    report = return_report(
        source,
        synthesize(source, mixed, 10),
        synthesize(source, bytes([0xFF]) * 8, 0),
        baseline,
        registration,
    )
    assert report["footer_mapping_prediction_matches_by_leg"] == [False, True]
    assert report["footer_plus_global_low4_scope_by_leg"] == [True, True]
    assert (
        report["literal_location_reports_against_FX7"][0]["raw_footer_projections"]["after"][
            "raw_footer_hex"
        ]
        == mixed.hex()
    )


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 8, 770, 3])
def test_footer_clear_cannot_rescue_hidden_pattern_changes(states, offset):
    _, source, baseline, registration = states
    clear = synthesize(source, bytes([0xFF]) * 8, 0)
    data = bytearray(pattern_data(clear, 1))
    data[offset] ^= 1
    actual = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(clear, 1, bytes(data)))
    )
    report = return_report(
        source, synthesize(source, bytes([0x77]) * 8, 10), actual, baseline, registration
    )
    assert report["footer_mapping_prediction_matches_by_leg"][1]
    assert not report["footer_plus_global_whole_byte_scope_by_leg"][1]
    assert not report["clear_matches_independent_no_FX_except_global131"]


@pytest.mark.capture
def test_other_global_change_and_stale_baseline_or_widened_candidate_fail(states):
    _, source, baseline, registration = states
    clear = synthesize(source, bytes([0xFF]) * 8, 0)
    packets = list(clear.packets)
    payload = bytearray(packets[2].payload)
    payload[132] ^= 1
    packets[2] = Packet(packets[2].tag, bytes(payload))
    other_global = decode_frame(bytes(4095) + encode_packets(packets))
    report = return_report(source, source, other_global, baseline, registration)
    assert not report["footer_plus_global_whole_byte_scope_by_leg"][1]
    assert not report["clear_matches_independent_no_FX_except_global131"]
    stale = copy.deepcopy(registration)
    stale["independent_no_FX_body_sha256"] = "0" * 64
    assert not return_report(source, source, clear, baseline, stale)[
        "independent_no_FX_body_matches_registration"
    ]
    altered = copy.deepcopy(registration)
    altered["global_candidate"]["payload_offset"] = 132
    with pytest.raises(ValueError, match="fixed preregistered"):
        return_report(source, source, clear, baseline, altered)
