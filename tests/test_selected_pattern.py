import pytest
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.edits import OPERATIONS
from po33_re.formats.globals import (
    pattern_chain,
    selected_pattern,
    set_pattern_chain,
    set_selected_pattern,
    set_swing,
    set_tempo,
    swing,
    tempo,
)
from po33_re.formats.packets import Packet, decode_frame, encode_packets
from po33_re.formats.patterns import copy_pattern, melodic_notes, pattern_data
from scripts.prepare_selected_pattern_test import MODELS, absolute_decision, reversed_keys


def frame():
    packets = list(synthetic_packets(patterns={1: pattern_bytes([(1, 3, "0d0981", 0xF0)])}))
    second = bytearray(255)
    second[129] = 120
    second[128] = 1
    packets[2] = Packet(0x7D5C, bytes(second))
    packets[1] = Packet(0x7D5C, bytes(255))
    return decode_frame(encode_packets(packets), start=0)


def decoded(packets):
    return decode_frame(encode_packets(packets), start=0)


def test_selected_pattern_round_trip_keeps_other_bytes():
    base = frame()
    assert selected_pattern(base) == 1
    edited = decoded(set_selected_pattern(base, 5))
    assert selected_pattern(edited) == 5
    assert edited.packets[2].payload[1:] == base.packets[2].payload[1:]
    with pytest.raises(ValueError, match="1..16"):
        set_selected_pattern(base, 17)


def test_copy_pattern_copies_every_byte():
    base = frame()
    edited = decoded(copy_pattern(base, 1, 5))
    assert pattern_data(edited, 5) == pattern_data(base, 1)
    assert melodic_notes(edited, 5, 3) == [1] + [None] * 15
    with pytest.raises(ValueError, match="differ"):
        copy_pattern(base, 2, 2)
    assert set(OPERATIONS["copy_pattern"][0]) == {"source_pattern", "destination_pattern"}


def test_models():
    assert reversed_keys(8)[0] == 1 and reversed_keys(1)[14] == 1
    assert MODELS["pattern5_selected"][2] == -150.0
    assert absolute_decision(1099.0)["classification"] == "pattern5_selected"
    assert absolute_decision(599.3)["classification"] == "pattern1_plays"


def test_chain_entries_and_length():
    base = frame()
    edited = decoded(set_pattern_chain(base, [5, 1, 1]))
    assert pattern_chain(edited) == [5, 1, 1] and selected_pattern(edited) == 5
    payload = edited.packets[2].payload
    assert list(payload[:3]) == [4, 0, 0] and payload[128] == 3
    assert payload[129:] == base.packets[2].payload[129:]
    single = decoded(set_selected_pattern(edited, 2))
    assert pattern_chain(single) == [2]
    assert single.packets[2].payload[1:3] == bytes([0, 0])
    for bad in ([], [17], [1] * 129):
        with pytest.raises(ValueError, match="Chain"):
            set_pattern_chain(base, bad)


def test_generic_swing_writer_ignores_the_opaque_context_guard():
    base = decoded(set_pattern_chain(frame(), [5, 1]))
    edited = decoded(set_swing(base, 18))
    assert swing(edited) == 18 and pattern_chain(edited) == [5, 1]
    assert edited.packets[2].payload[129] == 120
    with pytest.raises(ValueError, match="0 to 18"):
        set_swing(base, 19)
    assert OPERATIONS["set_swing_byte"][0] == {"value"}


def test_generic_tempo_writer():
    base = decoded(set_pattern_chain(frame(), [5, 1]))
    edited = decoded(set_tempo(base, 100))
    assert tempo(edited) == 100 and swing(edited) == 0 and pattern_chain(edited) == [5, 1]
    with pytest.raises(ValueError, match="60 to 240"):
        set_tempo(base, 300)
    assert OPERATIONS["set_tempo_byte"][0] == {"bpm"}
