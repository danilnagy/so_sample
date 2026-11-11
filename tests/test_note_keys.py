import hashlib
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import (
    END_TAG,
    START_TAG,
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
)
from po33_re.formats.patterns import pattern_data, set_melodic_key
from po33_re.modem.clock_decode import decode_clock_wav
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact


def note_frame(step=5, primary=b"\x0d\xf8\x83", auxiliary=0xF0, extra_cell=False):
    packets = [Packet(START_TAG, b"")]
    for pattern in range(16):
        packets.append(Packet(0xA041, bytes([pattern])))
        data = bytearray(1024) + bytes([255]) * 8
        if pattern == 0:
            p, a = 48 * (step - 1), 768 + 16 * (step - 1)
            data[p + 6 : p + 9] = primary
            data[a + 2] = auxiliary
            if extra_cell:
                data[p + 24 : p + 27] = bytes.fromhex("cff683")
                data[a + 8] = 16
        packets.extend(Packet(0xC498, bytes(data[i : i + 255])) for i in range(0, len(data), 255))
    packets.append(Packet(END_TAG, b""))
    return decode_frame(encode_packets(packets), start=0)


@pytest.mark.parametrize("step", [5, 13, 16])
@pytest.mark.parametrize("key,expected", [(1, 240), (2, 241), (7, 246), (16, 255)])
def test_key_edit_changes_one_byte_and_preserves_every_other_byte(step, key, expected):
    frame = note_frame(step=step)
    source = encode_packets(frame.packets)
    packets = set_melodic_key(frame, 1, step, 3, key)
    edited = decode_frame(encode_packets(packets), start=0)
    before, after = pattern_data(frame, 1), pattern_data(edited, 1)
    assert [(i, a, b) for i, (a, b) in enumerate(zip(before, after)) if a != b] == (
        [] if key == 1 else [(768 + 16 * (step - 1) + 2, 240, expected)]
    )
    assert encode_packets(set_melodic_key(edited, 1, step, 3, 1)) == source
    assert set_melodic_key(frame, 1, step, 3, 1) == frame.packets
    assert encode_packets(frame.packets) == source
    for a, b in zip(frame.packets, packets):
        assert a.tag == b.tag and len(a.payload) == len(b.payload)
    for slot in range(2, 17):
        assert pattern_data(frame, slot) == pattern_data(edited, slot)


@pytest.mark.parametrize(
    "step,sound,key",
    [(0, 3, 2), (17, 3, 2), (5, 4, 2), (5, 3, 0), (5, 3, 3), (5, 3, 17), (5, 3, True)],
)
def test_key_edit_rejects_untested_keys_sounds_and_invalid_steps(step, sound, key):
    with pytest.raises(ValueError):
        set_melodic_key(note_frame(), 1, step, sound, key)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"primary": bytes(3)},
        {"primary": bytes.fromhex("0df884")},
        {"auxiliary": 0xE0},
        {"auxiliary": 0xF2},
        {"extra_cell": True},
    ],
)
def test_key_edit_rejects_unobserved_or_unoccupied_source_cells(kwargs):
    frame = note_frame(**kwargs)
    before = encode_packets(frame.packets)
    with pytest.raises(ValueError):
        set_melodic_key(frame, 1, 5, 3, 2)
    assert encode_packets(frame.packets) == before


@pytest.mark.capture
def test_key_writer_reproduces_genuine_physical_control_and_inverse():
    root = Path(__file__).resolve().parents[1]
    base = root / "experiments/edited-pattern-001/derived/analysis-001/capture.symbols.npz"
    capture = root / "experiments/event-008-b-melodic-key2/capture.wav"
    if not base.exists() or not capture.exists():
        pytest.skip("Genuine four-note baseline and key2 control WAV required")
    assert (
        sha256_file(capture) == "ff78fa4c5b29b4b1ec4df8fdfa89cec54020da7e9059b3b342c78672edd9d90d"
    )
    source = load_artifact(base)
    unchanged = source.to_bytes()
    original = decode_artifact(source)
    actual = decode_artifact(decode_wav(capture, 0.0063))
    assert hashlib.sha256(actual.encoded_body).hexdigest() == (
        "82d11b01d01f04708b099c3e36f50f2474c09a2aaa85fa68f2511286a0159307"
    )
    assert encode_packets(set_melodic_key(original, 1, 5, 3, 2)) == actual.encoded_body
    assert encode_packets(set_melodic_key(actual, 1, 5, 3, 1)) == original.encoded_body
    assert [i for i, (a, b) in enumerate(zip(original.packets, actual.packets)) if a != b] == [7]
    assert source.to_bytes() == unchanged


@pytest.mark.capture
def test_genuine_key16_endpoint_matches_registered_byte_and_preserves_other_data():
    root = Path(__file__).resolve().parents[1]
    base_path = root / "experiments/edited-note-key-001/derived/analysis-002/capture.symbols.npz"
    directory = root / "experiments/event-009-b-melodic-key16"
    capture, acquisition_path = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    if not all(p.exists() for p in (base_path, capture, acquisition_path)):
        pytest.skip("Genuine alternating baseline and key16 recording/acquisition required")
    assert (
        sha256_file(capture) == "a0c0bea848c7c1bf56349e695edaae8740cd465d6df044512972d6c45ed5c0f1"
    )
    base = decode_artifact(load_artifact(base_path))
    acquisition = load_artifact(acquisition_path)
    unchanged = acquisition.to_bytes()
    with pytest.raises(ValueError, match="wire byte17902"):
        decode_artifact(acquisition)
    artifact, report = decode_clock_wav(capture, acquisition)
    actual = decode_artifact(artifact)
    assert acquisition.to_bytes() == unchanged
    assert report["target_data_used"] is False
    assert len(actual.packets) == 511 and actual.end_byte == 89396
    assert hashlib.sha256(actual.encoded_body).hexdigest() == (
        "55311018711e4b4b798609ce7c40bedb613d6dbb246ea2423aea8b8049db9fe9"
    )
    before, after = pattern_data(base, 1), pattern_data(actual, 1)
    assert [(i, a, b) for i, (a, b) in enumerate(zip(before, after)) if a != b] == [(834, 241, 255)]
    assert [i for i, (a, b) in enumerate(zip(base.packets, actual.packets)) if a != b] == [7]
    assert before[:768] == after[:768]


@pytest.mark.capture
def test_four_calibrated_keys_reproduce_genuine_endpoint_and_middle_controls():
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "experiments/edited-note-key-001/derived/analysis-002/capture.symbols.npz",
        root / "experiments/event-009-b-melodic-key16/derived/analysis-002/capture.symbols.npz",
        root / "experiments/event-010-b-melodic-key7/capture.wav",
    ]
    if not all(p.exists() for p in paths):
        pytest.skip("Genuine alternating, endpoint and middle-key controls required")
    assert (
        sha256_file(paths[2]) == "19d2e80e347e229081a8363668807a5ca269f8645820d59224a3f6d974cb245c"
    )
    alternating, endpoint = [decode_artifact(load_artifact(p)) for p in paths[:2]]
    middle = decode_artifact(decode_wav(paths[2], 0.0063))
    assert hashlib.sha256(middle.encoded_body).hexdigest() == (
        "6b4f5fd40b5b7c66a754c7a6f2d870015e69e225f24a2fe9730a6f3a135705ff"
    )
    assert encode_packets(set_melodic_key(alternating, 1, 5, 3, 16)) == endpoint.encoded_body
    assert encode_packets(set_melodic_key(endpoint, 1, 5, 3, 7)) == middle.encoded_body
    assert encode_packets(set_melodic_key(middle, 1, 5, 3, 16)) == endpoint.encoded_body
    assert encode_packets(set_melodic_key(middle, 1, 5, 3, 2)) == alternating.encoded_body
    before, after = pattern_data(endpoint, 1), pattern_data(middle, 1)
    assert [(i, a, b) for i, (a, b) in enumerate(zip(before, after)) if a != b] == [(834, 255, 246)]
