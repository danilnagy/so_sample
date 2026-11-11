import pytest
from test_drum_import import empty_frame
from test_sample_memory_step3 import ref, with_records

from po33_re.edits import OPERATIONS
from po33_re.formats.packets import (
    decode_frame,
    encode_packets,
    set_sample_window,
    sound_data,
)


def test_window_is_written_into_the_header_only():
    frame = with_records(empty_frame(), {5: ref(0, 4000, 5) + bytes(4096), 6: ref(0, 100, 5)})
    edited = decode_frame(encode_packets(set_sample_window(frame, 6, 1000, 2000)), start=0)
    data = sound_data(edited, 5)
    assert (
        int.from_bytes(data[:4], "little") == 1000 and int.from_bytes(data[4:8], "little") == 2000
    )
    assert data[8:] == sound_data(frame, 5)[8:]
    assert sound_data(edited, 6) == sound_data(frame, 6)
    assert OPERATIONS["set_sample_window"][0] == {"sound", "start", "end"}
    with pytest.raises(ValueError, match="own"):
        set_sample_window(frame, 7, 0, 10)
    for start, end in ((-1, 10), (10, 10), (0, 4097)):
        with pytest.raises(ValueError, match="Window"):
            set_sample_window(frame, 6, start, end)
