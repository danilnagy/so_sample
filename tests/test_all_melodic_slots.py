import numpy as np
import pytest
from test_drum_import import empty_frame
from test_sample_memory_step3 import ref, with_records

from po33_re.formats.packets import decode_frame, encode_packets, sound_data
from po33_re.sample_import import DEVICE_SAMPLE_LIMIT, import_melodic_sample_packets
from scripts.prepare_all_melodic_slots_test import MODELS, TONE_HZ, absolute_decision, keys_for


def test_borrowed_melodic_slot_gets_its_own_buffer():
    lender = ref(0, 4096, 0) + bytes(4096)
    frame = with_records(empty_frame(), {0: lender, 1: ref(0, 4096, 0)})
    with pytest.raises(ValueError, match="references another buffer"):
        import_melodic_sample_packets(frame, 2, np.zeros(3000), None, (2,), DEVICE_SAMPLE_LIMIT)
    with pytest.raises(ValueError, match="referrers"):
        import_melodic_sample_packets(
            frame, 1, np.zeros(3000), None, (1,), DEVICE_SAMPLE_LIMIT, 3000, True, True
        )
    packets, allocation = import_melodic_sample_packets(
        frame, 2, np.zeros(3000), None, (2,), DEVICE_SAMPLE_LIMIT, 3000, True, True
    )
    edited = decode_frame(encode_packets(packets), start=0)
    assert allocation["source_record_was_borrowed"] and allocation["capacity_codes"] == 4096
    assert sound_data(edited, 1)[8] == 1 and sound_data(edited, 0) == lender


def test_plan():
    assert keys_for(1)[0] == 1 and keys_for(8)[14] == 1 and sum(map(bool, keys_for(3))) == 1
    assert MODELS["slot_s_plays_its_tone"][:4] == [0.0, 0.0, 150.0, 150.0]
    assert TONE_HZ[1] == 400.0 and absolute_decision(599.3)["holds"]
