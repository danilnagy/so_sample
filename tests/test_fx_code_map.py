from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.formats.packets import decode_frame, encode_packets
from scripts.check_fx_code_map import decide, footer_codes, map_keys

REGISTRATION = {
    "assignments": {str(k): k + 1 for k in range(1, 16)},
    "predicted_codes": {str(k): f"{k - 1:X}" for k in range(1, 16)},
    "known_controls": {"7": "6", "8": "7"},
}


def frame_with(footers):
    patterns = {p: pattern_bytes([], footer=f) for p, f in footers.items()}
    return decode_frame(encode_packets(synthetic_packets(patterns=patterns)), start=0)


def uniform(code):
    return bytes([(code << 4) | code]) * 8


def test_footer_codes_are_high_nibble_first():
    assert "".join(footer_codes(bytes.fromhex("f6ffffffffff6fff"))) == "F6FFFFFFFFFF6FFF"


def test_full_key_minus_one_map_is_supported():
    footers = {k + 1: uniform(k - 1) for k in range(1, 16)}
    keys = map_keys(frame_with(footers), REGISTRATION)
    assert all(item["steps_with_effect"] == 16 for item in keys.values())
    assert decide(keys, REGISTRATION)["classification"] == "key_minus_one"


def test_partial_coverage_still_maps_and_a_wrong_code_fails():
    footers = {k + 1: uniform(k - 1) for k in range(1, 16)}
    footers[2] = bytes.fromhex("00ffffffffffffff")
    footers[11] = uniform(0xB)
    keys = map_keys(frame_with(footers), REGISTRATION)
    assert keys["1"]["mapped_code"] == "0" and keys["1"]["steps_with_effect"] == 2
    assert keys["10"]["mapped_code"] == "B" and not keys["10"]["matches_prediction"]
    result = decide(keys, REGISTRATION)
    assert result["controls_match"] and result["classification"] == "not_supported_or_partial"


def test_mixed_or_missing_codes_do_not_map():
    keys = map_keys(frame_with({3: bytes.fromhex("1122ffffffffffff")}), REGISTRATION)
    assert keys["2"]["mapped_code"] is None and keys["2"]["codes"] == ["1", "2"]
    assert keys["3"]["codes"] == [] and keys["3"]["mapped_code"] is None
