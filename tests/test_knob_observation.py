from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.formats.packets import Packet, decode_frame, encode_packets
from scripts.check_knob_observation import cell_changes, classify


def frame(patterns=None, second_byte=None):
    packets = list(synthetic_packets(patterns=patterns or {}))
    if second_byte is not None:
        payload = bytearray(packets[2].payload)
        payload[second_byte] ^= 1
        packets[2] = Packet(0x7D5C, bytes(payload))
    return decode_frame(encode_packets(packets), start=0)


def test_outcomes():
    base = frame({1: pattern_bytes([(1, 16, "0d0981", 0x10)])})
    assert classify(base, base)[0] == "nothing_stored"
    knob = frame({1: pattern_bytes([(1, 16, "0d0f81", 0x10)])})
    outcome, details = classify(base, knob)
    assert outcome == "sound16_cells_only"
    assert details["pattern_byte_changes"][0][:4] == [1, "primary", 1, 16]
    assert classify(base, frame({1: pattern_bytes([(1, 16, "0d0981", 0x10)])}, 50))[0] == (
        "global_records_only"
    )
    other = frame({1: pattern_bytes([(1, 3, "0d0981", 0xF0), (1, 16, "0d0981", 0x10)])})
    assert classify(base, other)[0] == "mixed"
    assert cell_changes(base, other)[0][3] == 3
