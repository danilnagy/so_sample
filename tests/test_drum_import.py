import io

import numpy as np
import pytest
import soundfile as sf

from po33_re.drum_import import drum_ids, drum_windows, import_drum_kit_packets
from po33_re.formats.packets import (
    END_TAG,
    START_TAG,
    Packet,
    decode_frame,
    encode_packets,
    sound_data,
)
from po33_re.formats.samples import encode_signed_mulaw
from po33_re.sample_import import prepare_pcm_sample
from scripts.drum_slice_duration_method import decide
from scripts.prepare_drum_kit_import_test import DURATION_MODEL_MS, LENGTHS, hit_wav


def empty_frame():
    packets = [Packet(START_TAG, b"")]
    packets += [Packet(0x68B5, bytes([sid])) for sid in range(136)]
    for n in range(16):
        packets.append(Packet(0xA041, bytes([n])))
        body = bytes(1024) + bytes([255] * 8)
        packets.extend(Packet(0xC498, body[i : i + 255]) for i in range(0, 1032, 255))
    packets.append(Packet(END_TAG, b""))
    return decode_frame(encode_packets(packets), start=0)


def hits(lengths):
    rng = np.random.default_rng(1)
    return [rng.uniform(-0.5, 0.5, n) for n in lengths]


def test_kit_layout_matches_the_device_recording():
    frame = empty_frame()
    lengths = [500 + 10 * k for k in range(16)]
    packets, allocation = import_drum_kit_packets(frame, 11, hits(lengths))
    edited = decode_frame(encode_packets(packets), start=0)
    windows = drum_windows(edited, 11)
    assert windows[0] == (0, 500, 40) and windows[1] == (500, 1010, 40)
    assert all(windows[k][1] == windows[k + 1][0] for k in range(15))
    assert len(sound_data(edited, 40)) == 9 + 12288  # 9200 codes rounded up to pages
    assert all(len(sound_data(edited, sid)) == 9 for sid in range(41, 56))
    assert allocation["kit_codes"] == sum(lengths) and allocation["source_kit_was_empty"]


def test_reimport_replaces_the_kit_and_keeps_its_codes_exact():
    frame = empty_frame()
    first = decode_frame(
        encode_packets(import_drum_kit_packets(frame, 11, hits([600] * 16))[0]), start=0
    )
    new = hits([700] * 16)
    packets, allocation = import_drum_kit_packets(first, 11, new)
    edited = decode_frame(encode_packets(packets), start=0)
    codes = np.frombuffer(sound_data(edited, 40)[9:], dtype=np.uint8)
    expected = np.concatenate([encode_signed_mulaw(h) for h in new])
    assert np.array_equal(codes[: len(expected)], expected) and not codes[len(expected) :].any()
    assert not allocation["source_kit_was_empty"] and len(packets) == len(first.packets)


def test_invalid_kits_are_rejected():
    frame = empty_frame()
    with pytest.raises(ValueError, match="one of"):
        import_drum_kit_packets(frame, 12, hits([600] * 16))
    with pytest.raises(ValueError, match="16 hits"):
        import_drum_kit_packets(frame, 11, hits([600] * 15))
    with pytest.raises(ValueError, match="frames"):
        import_drum_kit_packets(frame, 11, hits([100] + [600] * 15))
    with pytest.raises(ValueError, match="capacity"):
        import_drum_kit_packets(frame, 11, hits([7000] * 16))
    assert drum_ids(16) == list(range(120, 136))


def test_generated_hits_resample_to_the_planned_lengths():
    for key in (1, 16):
        native, _ = prepare_pcm_sample(hit_wav(1000.0, LENGTHS[key - 1]), None, (470, 102400))
        assert len(native) == LENGTHS[key - 1]
    samples, rate = sf.read(io.BytesIO(hit_wav(1000.0, 1750)))
    assert rate == 48000 and len(samples) == 3584


def test_duration_decision():
    good = {k: [v + 1.0] * 5 for k, v in enumerate(DURATION_MODEL_MS, 1)}
    assert decide(good, DURATION_MODEL_MS)["holds"]
    bad = {**good, 16: [250.0] * 5}
    assert not decide(bad, DURATION_MODEL_MS)["holds"]


def test_capacity_is_whole_pages_up_to_the_observed_maximum():
    frame = empty_frame()
    packets, allocation = import_drum_kit_packets(frame, 11, hits([600] * 16), 102400)
    assert allocation["capacity_codes"] == 102400
    for bad in (10000, 8192, 106496):
        with pytest.raises(ValueError, match="pages"):
            import_drum_kit_packets(frame, 11, hits([600] * 16), bad)
    packets, allocation = import_drum_kit_packets(frame, 12, hits([600] * 16), None, (12,))
    edited = decode_frame(encode_packets(packets), start=0)
    assert drum_windows(edited, 12)[0] == (0, 600, 56) and allocation["capacity_codes"] == 12288
