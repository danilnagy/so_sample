"""Retain failed four-bit minimum and compare independent predeclared interior models."""

import json
from pathlib import Path

import pytest

from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_volume_lock_range import range_checks
from scripts.check_sound3_volume_middle_series import series_checks


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-volume-middle-series-registration-001.json"
    if not path.exists():
        pytest.skip("Preserved minimum/return and interior registration required")
    registration = json.loads(path.read_text())
    maximum, minimum = [
        decode_artifact(load_artifact(root / registration[name]))
        for name in ("baseline_artifact", "minimum_endpoint_artifact")
    ]
    return root, maximum, minimum, registration


def synthetic_value(maximum, value, reversed_order=False):
    data = bytearray(pattern_data(maximum, 1))
    first, second = (value >> 4, value & 15) if reversed_order else (value & 3, value >> 2)
    for step in range(16):
        data[48 * step + 6] = (data[48 * step + 6] & 0x3F) | (first << 6)
        data[48 * step + 7] = (data[48 * step + 7] & 0xF0) | second
    return decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(maximum, 1, bytes(data)))
    )


@pytest.mark.capture
def test_actual_minimum_falsifies_old_mask_and_exact_maximum_return_remains_true(states):
    root, maximum, minimum, _ = states
    old = json.loads(
        (root / "experiments/sound3-volume-lock-range-registration-001.json").read_text()
    )
    result = range_checks(maximum, minimum, maximum, old)
    assert result["control_passed"] and not result["low_nibble_minimum_and_exact_return_supported"]
    assert result["hypothesis_checks"]["minimum_all16_raw_nibbles_zero"]
    assert not result["minimum_preservation_checks"][
        "all_pattern1_bits_except_candidate_low_nibbles_unchanged"
    ]
    assert result["hypothesis_checks"]["complete_return_body_equals_independent_original_maximum"]


@pytest.mark.capture
def test_contiguous_value_and_auxiliary_position_bands_are_separate_evidence(states):
    _, maximum, minimum, reg = states
    frames = [synthetic_value(maximum, 16), synthetic_value(maximum, 32), maximum]
    result = series_checks(maximum, minimum, frames, reg)
    assert result["all_field_scope_and_return_checks_pass"]
    little, other = result["encoding_models"].values()
    assert (
        little["field_scope_and_relative_order_supported"]
        and other["field_scope_and_relative_order_supported"]
    )
    assert (
        little["auxiliary_mechanical_position_bands_match"]
        and not other["auxiliary_mechanical_position_bands_match"]
    )
    assert not result["four_bit_value_with_zero_nonzero_enable_pair"]["supported_with_preservation"]
    assert (
        not result["gain_curve_or_packed_order_definitively_confirmed"]
        and not result["volume_writer_enabled"]
    )


@pytest.mark.capture
def test_alternative_ordering_is_evaluated_independently_without_preferring_little_endian(states):
    _, maximum, minimum, reg = states
    result = series_checks(
        maximum,
        minimum,
        [synthetic_value(maximum, 16, True), synthetic_value(maximum, 32, True), maximum],
        reg,
    )
    assert result["candidate_model_preferences_from_auxiliary_position_bands"] == [
        "two_first_byte_bits_are_most_significant"
    ]
    assert result["interior_has_first_byte_pair01_or10"]


@pytest.mark.capture
def test_fraction_bits_may_remain_unresolved_if_all_recorded_pairs_match_enable_alternative(states):
    _, maximum, minimum, reg = states
    result = series_checks(
        maximum, minimum, [synthetic_value(maximum, 19), synthetic_value(maximum, 35), maximum], reg
    )
    assert result["four_bit_value_with_zero_nonzero_enable_pair"]["supported_with_preservation"]
    assert not result["interior_has_first_byte_pair01_or10"]
    assert not result["gain_curve_or_packed_order_definitively_confirmed"]


@pytest.mark.capture
def test_nonuniform_ramp_values_and_wrong_position_order_are_retained(states):
    _, maximum, minimum, reg = states
    q = synthetic_value(maximum, 16)
    data = bytearray(pattern_data(q, 1))
    data[6] |= 0x40
    nonuniform = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(q, 1, bytes(data)))
    )
    result = series_checks(
        maximum, minimum, [nonuniform, synthetic_value(maximum, 32), maximum], reg
    )
    assert result["all_field_scope_and_return_checks_pass"]
    assert not result["encoding_models"]["contiguous_little_endian_six_bit_value"][
        "all16_cells_uniform_at_each_position"
    ]
    result = series_checks(maximum, minimum, [synthetic_value(maximum, 32), q, maximum], reg)
    assert not result["encoding_models"]["contiguous_little_endian_six_bit_value"][
        "minimum_quarter_middle_maximum_strict_order"
    ]


@pytest.mark.capture
def test_auxiliary_change_or_widened_mask_cannot_hide_behind_correct_volume_values(states):
    _, maximum, minimum, reg = states
    q = synthetic_value(maximum, 16)
    data = bytearray(pattern_data(q, 1))
    data[786] ^= 1
    wrong = decode_frame(bytes(4095) + encode_packets(_replace_pattern_data(q, 1, bytes(data))))
    result = series_checks(maximum, minimum, [wrong, synthetic_value(maximum, 32), maximum], reg)
    assert not result["all_field_scope_and_return_checks_pass"]
    assert not result["encoding_models"]["contiguous_little_endian_six_bit_value"][
        "field_scope_and_relative_order_supported"
    ]
    widened = dict(reg, candidate=dict(reg["candidate"], first_primary_byte_mask=255))
    with pytest.raises(ValueError, match="preregistered masks"):
        series_checks(maximum, minimum, [q, q, maximum], widened)


@pytest.mark.capture
def test_incomplete_sequence_is_rejected_before_any_model_comparison(states):
    _, maximum, minimum, reg = states
    with pytest.raises(ValueError, match="Exactly quarter"):
        series_checks(maximum, minimum, [maximum, maximum], reg)
