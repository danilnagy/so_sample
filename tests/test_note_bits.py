from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.edits import OPERATIONS
from po33_re.formats.notes import decode_parameters, set_unknown_bits, unknown_bits
from po33_re.formats.packets import decode_frame, encode_packets
from po33_re.formats.patterns import pattern_data
from scripts.check_note_bits_test import bit5_only_difference
from scripts.prepare_note_bits_test import EXPECTED_HZ, MODELS, PATTERN, STEPS, held_pitches


def frame(cells):
    return decode_frame(
        encode_packets(synthetic_packets(patterns={PATTERN: pattern_bytes(cells)})), start=0
    )


def test_bit5_writer_round_trip_keeps_other_fields():
    base = frame([(1, 1, "0d0981", 0xF0), (2, 1, "0d0981", 0xF0)])
    edited = decode_frame(
        encode_packets(set_unknown_bits(base, PATTERN, 1, [None, 1] + [None] * 14)), start=0
    )
    assert unknown_bits(edited, PATTERN, 1)[:2] == [0, 1]
    before, after = pattern_data(base, PATTERN), pattern_data(edited, PATTERN)
    changed, original = decode_parameters(after[48:51]), decode_parameters(before[48:51])
    assert changed.pop("unknown_bit5") == 1 and original.pop("unknown_bit5") == 0
    assert changed == original
    assert after[48] == before[48] | 0x20 and after[:48] == before[:48]
    assert OPERATIONS["set_note_unknown_bits"][0] == {"pattern", "sound", "values"}
    assert bit5_only_difference(edited, base) is False  # step 2 is not a flagged step in STEPS


def test_bit5_only_difference_detects_a_cleared_flag():
    cells = [(s, 1, "0d0981", 0xF0) for s in STEPS]
    target = frame(cells)
    flags = [STEPS[s][1] if s in STEPS else None for s in range(1, 17)]
    target = decode_frame(encode_packets(set_unknown_bits(target, PATTERN, 1, flags)), start=0)
    cleared = frame(cells)
    assert bit5_only_difference(cleared, target)
    assert not bit5_only_difference(target, target)


def test_models_and_hold():
    held = held_pitches()
    assert held[3] == 19 and held[5] == 7 and held[11] == 1 and held[15] == 13
    assert all(len(v) == 16 for v in MODELS.values())
    assert MODELS["zero_holds_last_pitch"][2] == 600.0 and MODELS["zero_is_pitch_13"][2] == 0.0
    assert len(EXPECTED_HZ) == 16
