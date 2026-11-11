import io

import numpy as np
import soundfile as sf

from po33_re.formats.packets import END_TAG, START_TAG, Packet, decode_frame, encode_packets
from scripts.check_drum11_record_observation import evaluate
from scripts.prepare_drum11_record_observation import FREQUENCIES, SOUND11_IDS, burst_wav


def frame_with_sounds(records):
    packets = [Packet(START_TAG, b"")]
    for sid in range(60):
        packets.append(Packet(0x68B5, bytes([sid])))
        data = records.get(sid, b"")
        packets.extend(Packet(0xEF78, data[i : i + 255]) for i in range(0, len(data), 255))
    for n in range(16):
        packets.append(Packet(0xA041, bytes([n])))
        body = bytes(1024) + b"\xff" * 8
        packets.extend(Packet(0xC498, body[i : i + 255]) for i in range(0, 1032, 255))
    packets.append(Packet(END_TAG, b""))
    return decode_frame(encode_packets(packets), start=0)


def reference(start, end, owner):
    return start.to_bytes(4, "little") + end.to_bytes(4, "little") + bytes([owner])


def test_registered_layout_is_recognised():
    base = frame_with_sounds({0: reference(0, 100, 0) + bytes(4096)})
    recorded = {0: reference(0, 100, 0) + bytes(4096)}
    length = 1600
    for k, sid in enumerate(SOUND11_IDS):
        start, end = k * 100, k * 100 + 99
        if sid == 40:
            recorded[sid] = reference(start, end, 40) + bytes(4096)
        else:
            recorded[sid] = reference(start, end, 40)
    result = evaluate(base, frame_with_sounds(recorded))
    assert result["owner_sound_id"] == 40 and result["owner_capacity_codes"] == 4096
    assert all(result["hypotheses"].values())
    assert len(result["slice_windows"]) == 16 and length == 16 * 100


def test_missing_references_fail_the_layout_hypotheses():
    base = frame_with_sounds({})
    result = evaluate(base, frame_with_sounds({40: reference(0, 500, 40) + bytes(4096)}))
    assert result["hypotheses"]["new_self_owned_buffer"]
    assert not result["hypotheses"]["sixteen_references"]
    assert not result["hypotheses"]["equal_split"]


def test_burst_source_has_sixteen_distinct_tones():
    samples, rate = sf.read(io.BytesIO(burst_wav()))
    assert rate == 44100 and samples.shape[1] == 2
    assert abs(len(samples) / rate - 2.8) < 0.01
    assert len(set(FREQUENCIES)) == 16 and FREQUENCIES[0] == 400
    assert np.abs(samples).max() <= 0.26
