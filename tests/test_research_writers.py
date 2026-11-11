import pytest
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.edits import OPERATIONS
from po33_re.formats.packets import decode_frame, encode_packets
from po33_re.formats.patterns import pattern_data
from po33_re.formats.research import set_global_byte, set_raw_cell


def frame():
    return decode_frame(encode_packets(synthetic_packets(patterns={2: pattern_bytes([])})), start=0)


def test_raw_cell_and_global_byte():
    base = frame()
    edited = decode_frame(encode_packets(set_raw_cell(base, 2, 3, 8, "0df907", 0x20)), start=0)
    data = pattern_data(edited, 2)
    assert data[48 * 2 + 21 : 48 * 2 + 24].hex() == "0df907" and data[768 + 32 + 7] == 0x20
    edited = decode_frame(encode_packets(set_global_byte(edited, 1, 131, 9)), start=0)
    assert edited.packets[2].payload[131] == 9 and edited.packets[2].payload[129] == 120
    with pytest.raises(ValueError, match="Offset"):
        set_global_byte(base, 1, 500, 1)
    assert OPERATIONS["set_raw_cell"][0] == {"pattern", "step", "sound", "primary_hex", "auxiliary"}
    assert OPERATIONS["set_global_byte"][0] == {"ordinal", "offset", "value"}
