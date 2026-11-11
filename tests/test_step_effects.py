import pytest
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.edits import OPERATIONS
from po33_re.formats.effects import set_step_effects, step_effects
from po33_re.formats.packets import decode_frame, encode_packets
from po33_re.formats.patterns import pattern_data


def frame_with(patterns=None):
    return decode_frame(encode_packets(synthetic_packets(patterns=patterns or {})), start=0)


def test_writer_places_codes_high_nibble_first_and_round_trips():
    frame = frame_with({4: pattern_bytes([(1, 3, "0e0981", 0xF0)])})
    effects = [7, None, None, 8, 1, 15] + [None] * 9 + [12]
    packets = set_step_effects(frame, 4, effects)
    edited = decode_frame(encode_packets(packets), start=0)
    assert pattern_data(edited, 4)[1024:] == bytes.fromhex("6ff70e" + "ff" * 4 + "fb")
    assert step_effects(edited, 4) == effects
    # Only pattern 4's footer changed.
    before, after = pattern_data(frame, 4), pattern_data(edited, 4)
    assert before[:1024] == after[:1024]
    others = [p for p in range(1, 17) if p != 4]
    assert all(pattern_data(frame, p) == pattern_data(edited, p) for p in others)
    assert edited.packets[:3] == frame.packets[:3]


def test_confirmed_full_step_layout_is_reproduced():
    frame = frame_with()
    rising = {2, 3, 5, 6, 10, 11, 13, 14}
    effects = [7 if step in rising else None for step in range(1, 17)]
    edited = decode_frame(encode_packets(set_step_effects(frame, 1, effects)), start=0)
    assert pattern_data(edited, 1)[1024:].hex() == "f66f66fff66f66ff"


def test_reader_matches_the_device_code_map():
    footers = {k + 1: bytes([((k - 1) << 4) | (k - 1)]) * 8 for k in range(1, 16)}
    frame = frame_with({p: pattern_bytes([], footer=f) for p, f in footers.items()})
    for key in range(1, 16):
        assert step_effects(frame, key + 1) == [key] * 16
    assert step_effects(frame, 1) == [None] * 16


@pytest.mark.parametrize(
    "effects",
    [
        [None] * 15,
        [None] * 17,
        [0] + [None] * 15,
        [16] + [None] * 15,
        ["7"] + [None] * 15,
        (None,) * 16,
    ],
)
def test_invalid_effect_lists_are_rejected(effects):
    with pytest.raises(ValueError):
        set_step_effects(frame_with(), 1, effects)


def test_edit_plan_operation_is_registered():
    arguments, apply = OPERATIONS["set_step_effects"]
    assert arguments == {"pattern", "effects"}
    frame = frame_with()
    packets = apply(frame, {"pattern": 2, "effects": [None] * 15 + [15]})
    assert step_effects(decode_frame(encode_packets(packets), start=0), 2)[-1] == 15


def test_writer_test_predictions_follow_the_compiled_footer():
    from scripts.prepare_step_effects_writer_test import EFFECT_STEPS, effects_list, predictions

    frame = frame_with()
    edited = decode_frame(encode_packets(set_step_effects(frame, 1, effects_list())), start=0)
    footer = pattern_data(edited, 1)[1024:]
    assert footer.hex() == "6ff6ff666ff6ff66"
    high = predictions(footer)["sequential_high_nibble_first"]
    assert sorted(int(s) for s, c in high.items() if c == "effect") == list(EFFECT_STEPS)
