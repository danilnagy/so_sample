import pytest
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.edits import OPERATIONS
from po33_re.formats.notes import (
    decode_parameters,
    encode_parameters,
    set_step_parameters,
    step_parameters,
)
from po33_re.formats.packets import decode_frame, encode_packets
from po33_re.formats.patterns import pattern_data
from scripts.prepare_pitch_law_test import MODELS, PITCH_CODES


def test_decoder_matches_the_calibrated_sound3_values():
    assert decode_parameters(bytes.fromhex("0e0981")) == {
        "pitch": 14,
        "volume": 36,
        "filter": 16,
        "resonance": 32,
        "unknown_bit5": 0,
    }
    assert decode_parameters(bytes.fromhex("0df883"))["filter"] == 63


def test_encoder_changes_one_field_and_keeps_every_other_bit():
    original = bytes([0x2E, 0x09, 0x81])  # unknown bit 5 set
    for field, value in (("pitch", 1), ("volume", 63), ("filter", 0), ("resonance", 7)):
        changed = decode_parameters(encode_parameters(original, **{field: value}))
        expected = dict(decode_parameters(original), **{field: value})
        assert changed == expected and changed["unknown_bit5"] == 1


@pytest.mark.parametrize(
    ("field", "value"), [("pitch", -1), ("pitch", 26), ("volume", 64), ("filter", -1), ("tone", 1)]
)
def test_out_of_range_or_unknown_fields_are_rejected(field, value):
    with pytest.raises(ValueError):
        encode_parameters(bytes(3), **{field: value})


def frame_with(cells):
    return decode_frame(
        encode_packets(synthetic_packets(patterns={2: pattern_bytes(cells)})), start=0
    )


def test_writer_sets_per_step_values_only_on_notes():
    cells = [(s, 5, "0e0981", 0xF0) for s in (1, 2, 3)]
    frame = frame_with(cells)
    values = [20, None, 3] + [None] * 13
    edited = decode_frame(
        encode_packets(set_step_parameters(frame, 2, 5, "pitch", values)), start=0
    )
    pitches = [None if p is None else p["pitch"] for p in step_parameters(edited, 2, 5)]
    assert pitches[:4] == [20, 14, 3, None]
    before, after = pattern_data(frame, 2), pattern_data(edited, 2)
    assert before[768:] == after[768:]
    with pytest.raises(ValueError, match="no note"):
        set_step_parameters(frame, 2, 5, "pitch", [None] * 5 + [9] + [None] * 10)


def test_edit_plan_operation_and_pitch_law_models():
    arguments, apply = OPERATIONS["set_step_parameters"]
    assert arguments == {"pattern", "sound", "parameter", "values"}
    frame = frame_with([(1, 3, "0e0981", 0xF0)])
    packets = apply(
        frame, {"pattern": 2, "sound": 3, "parameter": "volume", "values": [10] + [None] * 15}
    )
    assert step_parameters(decode_frame(encode_packets(packets), start=0), 2, 3)[0]["volume"] == 10
    assert MODELS["semitone_per_code"][0] == 0 and min(PITCH_CODES) == 1 and max(PITCH_CODES) == 25
    assert len(set(PITCH_CODES)) == 16


def test_pitch_law_confirmation_uses_a_new_order_and_a_late_window():
    from scripts.prepare_pitch_law_confirm import MODELS as CONFIRM
    from scripts.prepare_pitch_law_confirm import PITCH_CODES as NEW
    from scripts.prepare_pitch_law_confirm import PREVIOUS_CODES, SETTINGS

    assert NEW != PREVIOUS_CODES and len(set(NEW)) == 16 and NEW[0] == 13
    assert min(SETTINGS["window_starts_ms"]) >= 50
    assert CONFIRM["semitone_per_code"] == [100 * (c - 13) for c in NEW]
    assert CONFIRM["previous_order_kept"] == [100 * (c - 13) for c in PREVIOUS_CODES]
