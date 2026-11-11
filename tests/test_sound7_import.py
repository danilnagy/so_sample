import io
import math

import numpy as np
import pytest
import soundfile as sf
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.formats.packets import Packet, decode_frame, encode_packets, sound_data
from po33_re.sample_import import import_melodic_sample_packets, import_sound6_packets
from scripts.prepare_sound7_import_test import MODELS, SOUND7_CENTS, tone_wav


def frame_with_empty_slots():
    packets = list(synthetic_packets(patterns={1: pattern_bytes([(1, 3, "0e0981", 0xF0)])}))
    # Replace the single synthetic sound with empty selectors for Sound6 and Sound7.
    packets = [p for p in packets if p.tag not in (0x68B5, 0xEF78)]
    packets[3:3] = [Packet(0x68B5, b"\x05"), Packet(0x68B5, b"\x06")]
    return decode_frame(encode_packets(packets), start=0)


def test_generic_importer_writes_sound7_with_its_own_owner_byte():
    frame = frame_with_empty_slots()
    native = np.sin(np.linspace(0, 200, 7031)) * 0.5
    packets, allocation = import_melodic_sample_packets(frame, 7, native, 32768, (7,))
    edited = decode_frame(encode_packets(packets), start=0)
    record = sound_data(edited, 6)
    assert record[:4] == bytes(4) and record[8] == 6
    assert int.from_bytes(record[4:8], "little") == 7031
    assert len(record) == 9 + 32768 and allocation["sound_slot"] == 7


def test_public_scope_is_sound6_and_sound7():
    frame = frame_with_empty_slots()
    native = np.zeros(2344)
    import_melodic_sample_packets(frame, 7, native)
    with pytest.raises(ValueError, match="one of"):
        import_melodic_sample_packets(frame, 8, native)
    with pytest.raises(ValueError, match="Sound6"):
        import_sound6_packets(frame, 7, native)
    packets, _ = import_sound6_packets(frame, 6, native)
    assert sound_data(decode_frame(encode_packets(packets), start=0), 5)[8] == 5


def test_test_tone_and_prediction():
    samples, rate = sf.read(io.BytesIO(tone_wav()))
    assert rate == 48000 and len(samples) == 14400
    spectrum = np.abs(np.fft.rfft(samples * np.hanning(len(samples)), 1 << 18))
    peak = np.argmax(spectrum) * rate / (1 << 18)
    assert abs(peak - 600) < 0.5
    assert SOUND7_CENTS == pytest.approx(1200 * math.log2(0.8))
    assert MODELS["imported_tone_on_even_steps"][:2] == [0.0, SOUND7_CENTS]
