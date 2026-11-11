from pathlib import Path

import numpy as np
import pytest

from po33_re.formats.packets import (
    END_TAG,
    START_TAG,
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    rebuild_labels,
    replace_reference_counter,
)
from po33_re.formats.samples import decode_signed_mulaw
from po33_re.modem.symbols import load_artifact


def reference_encoding(packets):
    # Independent bit-at-a-time CRC, including little-endian state trailers.
    state, result = 0x1D0F, bytearray()

    def append(raw):
        nonlocal state
        result.append((raw + (state % 256)) % 256)
        state ^= raw << 8
        for _ in range(8):
            state = ((state << 1) ^ (0x1021 if state & 0x8000 else 0)) & 0xFFFF

    for p in packets:
        for raw in p.tag.to_bytes(2, "little") + bytes([len(p.payload)]) + p.payload:
            append(raw)
        expected = state
        append(expected & 255)
        append(expected >> 8)
    return bytes(result)


def test_packet_encoder_matches_independent_crc_and_parser():
    packets = (Packet(START_TAG, b""), Packet(0xEF78, bytes(range(255))), Packet(END_TAG, b""))
    expected = reference_encoding(packets)
    assert encode_packets(packets) == expected
    frame = decode_frame(expected, start=0)
    assert frame.packets == packets
    assert frame.end_byte == len(expected)


def test_corruption_truncation_and_missing_final_marker_are_rejected():
    packets = (Packet(START_TAG, b""), Packet(0x68B5, b"\x02"), Packet(END_TAG, b""))
    encoded = reference_encoding(packets)
    damaged = bytearray(encoded)
    damaged[8] ^= 1
    for data in (bytes(damaged), encoded[:-1], encoded[:-5]):
        with pytest.raises(ValueError):
            decode_frame(data, start=0)
    with pytest.raises(ValueError):
        encode_packets((Packet(START_TAG, b""), Packet(0xEF78, bytes(256)), Packet(END_TAG, b"")))


def test_signed_mulaw_hand_values_and_negative_zero():
    codes = np.array([0x00, 0xFF, 0x01, 0xFE, 0x10, 0xEF, 0x7F, 0x80], dtype=np.uint8)
    assert (decode_signed_mulaw(codes) * 32768).tolist() == [0, 0, 8, -8, 132, -132, 32124, -32124]


@pytest.mark.capture
def test_genuine_trim_reencode_reproduces_held_out_packet_body_and_phase_prefix():
    root = Path(__file__).resolve().parents[1]
    base = (
        root / "experiments/empty-001-h-sound3-copy-return/derived/analysis-001/capture.symbols.npz"
    )
    control = (
        root / "experiments/empty-001-f-sound3-trim-min/derived/analysis-001/capture.symbols.npz"
    )
    if not base.exists() or not control.exists():
        pytest.skip("Controlled copied and minimum-length captures required")
    source, recorded = load_artifact(base), load_artifact(control)
    unchanged_source = source.to_bytes()
    original, minimum = decode_artifact(source), decode_artifact(recorded)
    assert len(original.packets) == len(minimum.packets) == 511
    assert original.end_byte == minimum.end_byte == 89396
    replacements = replace_reference_counter(original, 3, 79)
    assert replacements == minimum.packets
    assert encode_packets(replacements) == minimum.encoded_body
    rebuilt = rebuild_labels(source, replacements)
    required = 2 * minimum.end_byte + 3
    for ch in ("left", "right"):
        assert np.array_equal(
            getattr(rebuilt, ch + "_symbols")[:required],
            getattr(recorded, ch + "_symbols")[:required],
        )
    assert len(rebuilt.left_symbols) == len(rebuilt.right_symbols)
    for invalid in (0, 78, 65536):
        with pytest.raises(ValueError):
            replace_reference_counter(original, 3, invalid)
    assert source.to_bytes() == unchanged_source


@pytest.mark.capture
def test_genuine_post_restore_backup_has_registered_trim_and_unchanged_sample():
    from po33_re.artifacts import sha256_file
    from po33_re.formats.packets import sound_data
    from po33_re.modem.decode import decode_wav

    root = Path(__file__).resolve().parents[1]
    capture = root / "experiments/edited-trim-001/capture.wav"
    base = root / "experiments/empty-001-h-sound3-copy-return/capture.wav"
    if not capture.exists() or not base.exists():
        pytest.skip("Hardware trim recapture and original WAV required")
    assert (
        sha256_file(capture) == "e039a7ce9392e44827424134bee6f08439fd66cd45b2b7712759b4c89794bc0c"
    )
    import hashlib

    original = decode_artifact(decode_wav(base, 0.0063))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    assert hashlib.sha256(actual.encoded_body).hexdigest() == (
        "0191ad7ee47710d5bcb117d8b3d1c9774c972ff06df829f9cb302d2f2046c4d7"
    )
    assert actual.packets == replace_reference_counter(original, 3, 8000)
    assert sound_data(actual, 0)[9:] == sound_data(original, 0)[9:]
    assert len(actual.packets) == 511
    assert actual.end_byte == 89396
