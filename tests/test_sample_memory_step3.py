import numpy as np
import pytest
from test_drum_import import empty_frame, hits

from po33_re.drum_import import drum_windows, import_drum_kit_packets
from po33_re.formats.packets import Packet, decode_frame, encode_packets, sound_data
from scripts.prepare_sample_memory_step3 import FREQUENCIES, MODELS, TOTAL, absolute_decision


def with_records(frame, records):
    packets = []
    for packet in frame.packets:
        packets.append(packet)
        if packet.tag == 0x68B5 and packet.payload[0] in records:
            data = records[packet.payload[0]]
            packets.extend(Packet(0xEF78, data[i : i + 255]) for i in range(0, len(data), 255))
    return decode_frame(encode_packets(packets), start=0)


def ref(start, end, owner):
    return start.to_bytes(4, "little") + end.to_bytes(4, "little") + bytes([owner])


def test_borrowed_kit_gets_its_own_buffer_and_the_lender_is_kept():
    lender = ref(0, 4096, 0) + bytes(4096)
    records = {
        0: lender,
        **{sid: ref(100 * k, 100 * k + 99, 0) for k, sid in enumerate(range(8, 24))},
    }
    frame = with_records(empty_frame(), records)
    packets, allocation = import_drum_kit_packets(frame, 9, hits([600] * 16), None, (9,))
    edited = decode_frame(encode_packets(packets), start=0)
    assert allocation["source_layout"] == "references_to_sound_id_0"
    assert drum_windows(edited, 9)[0] == (0, 600, 8)
    assert sound_data(edited, 0) == lender


def test_borrowed_kit_must_reference_a_self_owned_buffer():
    records = {sid: ref(0, 99, 0) for sid in range(8, 24)}
    with pytest.raises(ValueError, match="not self-owned"):
        import_drum_kit_packets(
            with_records(empty_frame(), records), 9, hits([600] * 16), None, (9,)
        )


def test_step3_plan():
    assert TOTAL == 917504 and TOTAL < 937500
    assert FREQUENCIES[0] == 450.0 and MODELS["sound9_key_k"][15] == 1500.0
    assert absolute_decision(450.1)["stored_rate"] and not np.isnan(TOTAL)
