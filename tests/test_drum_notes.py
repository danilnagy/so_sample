import pytest
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.edits import OPERATIONS
from po33_re.formats.packets import decode_frame, encode_packets
from po33_re.formats.patterns import drum_notes, melodic_notes, pattern_data, set_drum_notes
from scripts.prepare_drum_notes_writer_test import MODELS, absolute_decision

NOTE = "0d0981"


def frame_with(cells):
    return decode_frame(
        encode_packets(synthetic_packets(patterns={1: pattern_bytes(cells)})), start=0
    )


def decoded(packets):
    return decode_frame(encode_packets(packets), start=0)


def test_writer_encodes_keys_as_0x10_plus_key_minus_one():
    frame = frame_with([(1, 3, NOTE, 0xF0)])
    keys = [1, 2, None, 16] + [None] * 11 + [9]
    edited = decoded(set_drum_notes(frame, 1, 11, keys, 3))
    assert drum_notes(edited, 1, 11) == keys
    data = pattern_data(edited, 1)
    assert data[768 + 10] == 0x10 and data[768 + 16 + 10] == 0x11
    assert data[768 + 48 + 10] == 0x1F and data[768 + 32 + 10] == 0
    assert data[30:33].hex() == NOTE and data[96 + 30 : 96 + 33] == bytes(3)
    assert melodic_notes(edited, 1, 3) == [1] + [None] * 15


def test_recorded_sound10_values_read_as_keys_1_and_2():
    frame = frame_with([(1, 10, "0df883", 0x10), (9, 10, "0df883", 0x11)])
    assert drum_notes(frame, 1, 10) == [1] + [None] * 7 + [2] + [None] * 7


def test_melodic_values_are_not_drum_notes():
    with pytest.raises(ValueError, match="not a drum note"):
        drum_notes(frame_with([(1, 11, NOTE, 0xF0)]), 1, 11)


@pytest.mark.parametrize(
    ("sound", "keys", "template", "message"),
    [
        (8, [1] * 16, 3, "Drum sound"),
        (11, [1] * 15, 3, "16 entries"),
        (11, [0] + [1] * 15, 3, "key 1..16"),
        (11, [1] * 16, 17, "Template"),
        (11, [1] * 16, 4, "identical"),
    ],
)
def test_invalid_arguments_are_rejected(sound, keys, template, message):
    with pytest.raises(ValueError, match=message):
        set_drum_notes(frame_with([(1, 3, NOTE, 0xF0)]), 1, sound, keys, template)


def test_plan_operation_and_registered_models():
    arguments, apply = OPERATIONS["set_drum_notes"]
    assert arguments == {"pattern", "sound", "keys", "template_sound"}
    frame = frame_with([(1, 3, NOTE, 0xF0)])
    edited = decoded(
        apply(frame, {"pattern": 1, "sound": 11, "keys": list(range(1, 17)), "template_sound": 3})
    )
    assert drum_notes(edited, 1, 11) == list(range(1, 17))
    assert MODELS["key_k_plays_slice_k"][15] == 2250.0
    assert absolute_decision(400.0)["classification"] == "stored_rate"
    assert absolute_decision(400 * 2 ** (7 / 12))["classification"] == "plus_7_semitones"
    assert absolute_decision(500.0)["classification"] == "other_or_inconclusive"
