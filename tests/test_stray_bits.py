from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.formats.packets import Packet, decode_frame, encode_packets
from po33_re.formats.research import set_global_byte, set_raw_cell
from scripts.check_stray_bits_test import cell_outcomes, global_outcomes, other_differences
from scripts.prepare_stray_bits_test import GLOBAL_BYTES, RAW_CELLS, VOICES


def base():
    packets = list(synthetic_packets(patterns={2: pattern_bytes([])}))
    for index in (1, 2):  # the device's global records are 255 bytes
        packets[index] = Packet(0x7D5C, packets[index].payload.ljust(255, b"\0"))
    return decode_frame(encode_packets(packets), start=0)


def target():
    packets = base().packets
    frame = base()
    for step, (sound, primary, auxiliary) in RAW_CELLS.items():
        packets = set_raw_cell(frame, 2, step, sound, primary, auxiliary)
        frame = decode_frame(encode_packets(packets), start=0)
    for offset, value in GLOBAL_BYTES.items():
        frame = decode_frame(encode_packets(set_global_byte(frame, 1, offset, value)), start=0)
    return frame


def test_outcomes_against_a_cleared_backup():
    t = target()
    assert all(v["outcome"] == "kept" for v in cell_outcomes(t, t).values())
    assert all(v["outcome"] == "kept" for v in global_outcomes(t, t).values())
    cleared = base()
    cells = cell_outcomes(cleared, t)
    assert all(v["outcome"] == "cleared" for v in cells.values())
    assert other_differences(cleared, t) == 0
    assert len(VOICES) == 3 and len(GLOBAL_BYTES) == 16
