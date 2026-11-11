"""FX footer location and nibble projections remain independent of guessed effect codes."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_pattern1_fx_probe import fx_report


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/pattern1-FX7-probe-registration-001.json"
    if not path.exists():
        pytest.skip("Registered FX probe required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


def synthesize(base, data, pattern=1):
    return decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(base, pattern, bytes(data)))
    )


@pytest.mark.capture
def test_genuine_resonance32_and_footer_baseline_are_pinned_before_FX_data(states):
    root, base, registration = states
    folder = root / "experiments/edited-sound3-filter16-B32-middle-001"
    observation = json.loads((folder / "hardware-observation-001.json").read_text())
    assert observation["hardware_verified"] and all(observation["checks"].values())
    assert (
        sha256_file(folder / "hardware-observation-001.json")
        == registration["source_observation_sha256"]
    )
    assert pattern_data(base, 1)[1024:] == bytes([255]) * 8
    assert registration["registered_before_recorded_FX_capture"]
    assert registration["raw_FX_code_prediction"] is None
    assert registration["official_effect_key"] == 7


@pytest.mark.capture
@pytest.mark.parametrize("value", [0, 6, 9, 14])
def test_footer_location_supported_for_unknown_uniform_codes_without_selecting_a_code(
    states, value
):
    _, base, registration = states
    data = bytearray(pattern_data(base, 1))
    data[1024:] = bytes([value | (value << 4)]) * 8
    report = fx_report(base, synthesize(base, data), registration)
    assert (
        report["actual_native_controls_pass"] and report["only_Pattern1_footer_changed_supported"]
    )
    assert report["Pattern1_primary_and_auxiliary_unchanged"]
    assert report["raw_footer_projections"]["after"]["low_nibble_first_values"] == [value] * 16
    assert not report["raw_FX_code_guessed"] and not report["FX_writer_enabled"]


@pytest.mark.capture
def test_mixed_footer_projections_are_literal_not_averaged(states):
    _, base, registration = states
    data = bytearray(pattern_data(base, 1))
    data[1024:] = bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xFF])
    report = fx_report(base, synthesize(base, data), registration)
    raw = report["raw_footer_projections"]["after"]
    assert raw["low_nibble_first_values"] == [2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 15, 15]
    assert raw["high_nibble_first_values"] == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        15,
    ]
    assert not report["after_footer_nibbles_uniform"]


@pytest.mark.capture
def test_no_change_remains_valid_native_evidence_without_footer_support(states):
    _, base, registration = states
    report = fx_report(base, base, registration)
    assert report["no_serialized_change"] and report["actual_native_controls_pass"]
    assert not report["only_Pattern1_footer_changed_supported"]


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 8, 770, 3])
def test_coupled_pattern1_changes_remain_broader_without_rescuing_footer_scope(states, offset):
    _, base, registration = states
    data = bytearray(pattern_data(base, 1))
    data[1024] = 0x66
    data[offset] ^= 1
    report = fx_report(base, synthesize(base, data), registration)
    assert report["actual_native_controls_pass"]
    assert report["broader_Pattern1_change_supported"]
    assert not report["only_Pattern1_footer_changed_supported"]


@pytest.mark.capture
def test_other_pattern_change_and_candidate_widening_or_stale_source_fail(states):
    _, base, registration = states
    data = bytearray(pattern_data(base, 2))
    data[1024] = 0x66
    report = fx_report(base, synthesize(base, data, 2), registration)
    assert not report["preservation_checks"]["other15_patterns_unchanged"]
    assert not report["only_Pattern1_footer_changed_supported"]
    altered = copy.deepcopy(registration)
    altered["footer_candidate"]["start_byte"] = 0
    with pytest.raises(ValueError, match="preregistered"):
        fx_report(base, base, altered)
    altered = copy.deepcopy(registration)
    altered["source_body_sha256"] = "0" * 64
    assert not fx_report(base, base, altered)["source_body_matches_registration"]
