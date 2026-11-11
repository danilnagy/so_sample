import pytest
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.edits import OPERATIONS
from po33_re.formats.packets import decode_frame, encode_packets
from po33_re.formats.patterns import (
    drum_notes,
    melodic_notes,
    pattern_data,
    set_melodic_notes,
    set_notes,
)
from scripts.prepare_melodic_notes_writer_test import MELODY, MODELS, cents_relative_to_step1

NOTE = "0e0981"


def frame_with(cells):
    return decode_frame(
        encode_packets(synthetic_packets(patterns={1: pattern_bytes(cells)})), start=0
    )


def test_reader_and_writer_round_trip_a_melody_with_rests():
    frame = frame_with([(1, 3, NOTE, 0xF0)])
    keys = [5, None, 16, 1] + [None] * 11 + [9]
    edited = decode_frame(encode_packets(set_melodic_notes(frame, 1, 3, keys)), start=0)
    assert melodic_notes(edited, 1, 3) == keys
    data = pattern_data(edited, 1)
    assert data[3 * 2 : 3 * 2 + 3].hex() == NOTE and data[768 + 2] == 0xF4
    assert data[48 + 6 : 48 + 9] == bytes(3) and data[768 + 16 + 2] == 0
    # Other sounds and the footer are untouched.
    before = pattern_data(frame, 1)
    other = [i for i in range(1032) if i % 48 not in (6, 7, 8) or i >= 768]
    assert all(data[i] == before[i] for i in other if i < 768 or (i - 768) % 16 != 2)


def test_writer_keeps_other_sounds_and_requires_one_template():
    frame = frame_with([(1, 3, NOTE, 0xF0), (2, 2, "0d2831", 0xF0)])
    edited = decode_frame(encode_packets(set_melodic_notes(frame, 1, 3, [2] * 16)), start=0)
    assert melodic_notes(edited, 1, 2) == [None, 1] + [None] * 14
    with pytest.raises(ValueError, match="identical"):
        set_melodic_notes(frame_with([]), 1, 3, [1] * 16)
    mixed = frame_with([(1, 3, NOTE, 0xF0), (2, 3, "0df883", 0xF0)])
    with pytest.raises(ValueError, match="identical"):
        set_melodic_notes(mixed, 1, 3, [1] * 16)


@pytest.mark.parametrize(
    ("sound", "keys", "message"),
    [
        (9, [1] * 16, "Melodic sound"),
        (3, [1] * 15, "16 entries"),
        (3, [0] + [1] * 15, "key 1..16"),
        (3, [17] + [1] * 15, "key 1..16"),
    ],
)
def test_invalid_arguments_are_rejected(sound, keys, message):
    with pytest.raises(ValueError, match=message):
        set_melodic_notes(frame_with([(1, 3, NOTE, 0xF0)]), 1, sound, keys)


def test_drum_auxiliary_values_are_not_read_as_melodic_notes():
    frame = frame_with([(1, 3, "0df883", 0x10)])
    with pytest.raises(ValueError, match="not a melodic note"):
        melodic_notes(frame, 1, 3)


def test_edit_plan_operation_and_writer_test_predictions():
    arguments, apply = OPERATIONS["set_melodic_notes"]
    assert arguments == {"pattern", "sound", "keys"}
    frame = frame_with([(1, 3, NOTE, 0xF0)])
    packets = apply(frame, {"pattern": 1, "sound": 3, "keys": MELODY})
    assert melodic_notes(decode_frame(encode_packets(packets), start=0), 1, 3) == MELODY
    assert MODELS["melody_written"][0] == 0
    assert cents_relative_to_step1([1, 4, 13])[1:] == [400, -1900]
    assert len(set(MELODY)) == 16


def test_notes_can_copy_parameters_from_another_sound():
    frame = frame_with([(1, 3, NOTE, 0xF0)])
    keys = [None, 1] * 8
    edited = decode_frame(
        encode_packets(set_melodic_notes(frame, 1, 7, keys, template_sound=3)), start=0
    )
    assert melodic_notes(edited, 1, 7) == keys
    assert melodic_notes(edited, 1, 3) == [1] + [None] * 15
    data = pattern_data(edited, 1)
    assert data[48 + 18 : 48 + 21].hex() == NOTE
    with pytest.raises(ValueError, match="identical"):
        set_melodic_notes(frame, 1, 7, keys)
    with pytest.raises(ValueError, match="Template sound"):
        set_melodic_notes(frame, 1, 7, keys, template_sound=17)
    drum = frame_with([(1, 11, NOTE, 0x10)])
    from_drum = decode_frame(
        encode_packets(set_melodic_notes(drum, 1, 6, [1] + [None] * 15, template_sound=11)),
        start=0,
    )
    assert melodic_notes(from_drum, 1, 6) == [1] + [None] * 15
    arguments, _ = OPERATIONS["set_melodic_notes_from"]
    assert arguments == {"pattern", "sound", "keys", "template_sound"}


def test_clearing_needs_no_template():
    frame = frame_with([(1, 3, NOTE, 0xF0)])
    cleared = decode_frame(encode_packets(set_melodic_notes(frame, 1, 7, [None] * 16)), start=0)
    assert melodic_notes(cleared, 1, 7) == [None] * 16
    assert melodic_notes(cleared, 1, 3) == [1] + [None] * 15


def test_explicit_parameter_writer_needs_no_template():
    params = {"pitch": 13, "volume": 36, "filter": 63, "resonance": 1}
    frame = frame_with([])
    edited = decode_frame(
        encode_packets(set_notes(frame, 1, 7, [1, None, 5] + [None] * 13, params)), start=0
    )
    assert melodic_notes(edited, 1, 7) == [1, None, 5] + [None] * 13
    data = pattern_data(edited, 1)
    assert data[18:21].hex() == "0df907" and data[768 + 6] == 0xF0
    drums = decode_frame(
        encode_packets(set_notes(edited, 1, 13, [2] + [None] * 15, params)), start=0
    )
    assert drum_notes(drums, 1, 13) == [2] + [None] * 15
    assert pattern_data(drums, 1)[768 + 12] == 0x11
    assert OPERATIONS["set_notes"][0] == {"pattern", "sound", "keys", "parameters"}
    with pytest.raises(ValueError, match="Parameters"):
        set_notes(frame, 1, 7, [1] * 16, {"pitch": 13})
