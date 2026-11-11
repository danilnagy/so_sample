import pytest
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.formats.packets import decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from scripts.check_pattern1_fx_order_single_tone import classify, first_tones
from scripts.pattern1_fx_nibble_audio import PARAMETERS, compare_audio
from scripts.prepare_pattern1_fx_order_single_tone import leg_checks, leg_pattern

REFERENCE = 1190.417
SINGLE_TONE = pattern_bytes([(1, 3, "0e0981", 0xF0)])
REGISTRATION = {
    "reference_relative_tolerance": 0.01,
    "predictions": {
        "low_nibble_first": {"a_frequency_hz": 2 * REFERENCE, "b_frequency_hz": REFERENCE},
        "high_nibble_first": {"a_frequency_hz": REFERENCE, "b_frequency_hz": 2 * REFERENCE},
    },
}


def frame_of(packets):
    return decode_frame(encode_packets(packets), start=0)


def report(hz, usable=True):
    return {
        "parameters": PARAMETERS,
        "passed": usable,
        "channels": {
            channel: {
                "measurements": [
                    {
                        "threshold_peak_fraction": fraction,
                        "usable": usable,
                        "fit": {"fit_success": usable, "frequency_hz": hz},
                    }
                    for fraction in PARAMETERS["threshold_peak_fractions"]
                ]
            }
            for channel in ("left", "right")
        },
    }


def decide(a_hz, b_hz, usable=True):
    a, b = report(a_hz, usable), report(b_hz, usable)
    return classify(compare_audio(a, b, PARAMETERS), a, b, REGISTRATION)


def test_leg_pattern_sets_only_footer_byte0():
    for footer in (0xF6, 0x6F):
        data = leg_pattern(SINGLE_TONE, footer)
        assert data[1024] == footer and data[:1024] == SINGLE_TONE[:1024]
        assert data[1025:] == b"\xff" * 7


def test_leg_pattern_rejects_other_sources():
    with pytest.raises(ValueError, match="clear"):
        leg_pattern(pattern_bytes([(1, 3, "0e0981", 0xF0)], footer=b"\x6f" + b"\xff" * 7), 0xF6)
    with pytest.raises(ValueError, match="single Sound3"):
        leg_pattern(pattern_bytes([(1, 3, "0e0981", 0xF0), (5, 3, "0e0981", 0xF1)]), 0xF6)


def test_leg_checks_accept_the_leg_and_reject_extra_changes():
    base = frame_of(synthetic_packets(patterns={1: SINGLE_TONE}))
    good = frame_of(_replace_pattern_data(base, 1, leg_pattern(SINGLE_TONE, 0xF6)))
    checks = leg_checks(base, good, 0xF6)
    # The synthetic source is not the real verified body; every other check passes.
    assert not checks.pop("source_is_verified_single_tone_body")
    assert all(checks.values())
    extra = bytearray(leg_pattern(SINGLE_TONE, 0xF6))
    extra[1025] = 0x7F
    bad = frame_of(_replace_pattern_data(base, 1, bytes(extra)))
    assert not leg_checks(base, bad, 0xF6)["only_footer_byte0_changed"]
    other_pattern = frame_of(
        _replace_pattern_data(good, 2, pattern_bytes([(1, 1, "0e0981", 0xF0)]))
    )
    assert not leg_checks(base, other_pattern, 0xF6)["only_Pattern1_data_changed"]
    assert pattern_data(good, 1)[6:9].hex() == "0e0981"


def test_low_nibble_first_needs_ratio_and_reference_agreement():
    result = decide(2 * REFERENCE, REFERENCE)
    assert result["primary_ratio_classification"] == "low_nibble_first"
    assert result["reference_cross_check"] == {"low_nibble_first": True, "high_nibble_first": False}
    assert result["classification"] == "low_nibble_first"


def test_high_nibble_first_is_supported_symmetrically():
    result = decide(REFERENCE * 1.002, 2 * REFERENCE * 0.998)
    assert result["classification"] == "high_nibble_first"


def test_ratio_without_reference_agreement_stays_inconclusive():
    # An octave apart, but both shifted away from the measured reference.
    result = decide(2 * REFERENCE * 1.05, REFERENCE * 1.05)
    assert result["primary_ratio_classification"] == "low_nibble_first"
    assert result["classification"] == "inconclusive"


def test_unusable_or_equal_tones_are_inconclusive():
    assert decide(REFERENCE, REFERENCE)["classification"] == "inconclusive"
    unusable = decide(2 * REFERENCE, REFERENCE, usable=False)
    assert unusable["classification"] == "inconclusive"
    assert first_tones(report(REFERENCE, usable=False)) == [None] * 6
