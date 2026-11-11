from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from po33_re.formats.packets import (
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_data,
    sound_groups,
)
from po33_re.formats.samples import decode_signed_mulaw, encode_signed_mulaw, replace_owner_codes
from po33_re.modem.symbols import load_artifact


def test_encoder_hand_values_and_all_representable_levels():
    values = np.array([0, 8, -8, 132, -132, 32124, -32124], dtype=float) / 32768
    assert encode_signed_mulaw(values).tolist() == [0x00, 0x01, 0xFE, 0x10, 0xEF, 0x7F, 0x80]
    all_codes = np.arange(255, dtype=np.uint8)
    assert np.array_equal(encode_signed_mulaw(decode_signed_mulaw(all_codes)), all_codes)
    assert encode_signed_mulaw(np.array([-1.0, 1.0])).tolist() == [0x80, 0x7F]
    assert encode_signed_mulaw(np.array([], dtype=float)).size == 0


@pytest.mark.parametrize(
    "invalid",
    [
        np.array([np.nan]),
        np.array([np.inf]),
        np.array([1.01]),
        np.array([0], dtype=int),
        np.zeros((2, 1)),
    ],
)
def test_encoder_rejects_invalid_audio(invalid):
    with pytest.raises(ValueError):
        encode_signed_mulaw(invalid)


def test_quantization_error_stays_within_half_local_step():
    # Independent analytic spacing: steps are8*2**exponent; segment edges
    # have a1.5-step gap to the next segment's first level.
    samples = 0.25 * np.sin(2 * np.pi * 750 * np.arange(46875) / 23437.5)
    codes = encode_signed_mulaw(samples)
    reconstructed = decode_signed_mulaw(codes)
    magnitude_code = np.minimum(codes, 255 - codes).astype(int)
    exponent = (magnitude_code >> 4) & 7
    edge = (magnitude_code % 16 == 15) & (exponent < 7)
    bound = (8 * 2**exponent) * np.where(edge, 0.75, 0.5) / 32768
    assert np.all(abs(reconstructed - samples) <= bound + 1e-12)
    assert np.sqrt(np.mean((reconstructed - samples) ** 2)) < 0.003


@pytest.mark.capture
def test_fixed_buffer_replacement_preserves_headers_and_unrelated_packets():
    path = Path(__file__).resolve().parents[1] / (
        "experiments/edited-trim-001/derived/analysis-001/capture.symbols.npz"
    )
    if not path.exists():
        pytest.skip("Hardware-verified trim artifact required")
    source = load_artifact(path)
    original_bytes = source.to_bytes()
    original = decode_artifact(source)
    owner = sound_data(original, 0)
    codes = np.frombuffer(owner[9:], dtype=np.uint8)
    assert replace_owner_codes(original, 1, codes) == original.packets
    replacement = np.zeros(len(codes), dtype=np.uint8)
    packets = replace_owner_codes(original, 1, replacement)
    updated = decode_frame(encode_packets(packets), start=0)
    assert sound_data(updated, 0) == owner[:9] + bytes(len(codes))
    allowed = set(sound_groups(original)[0])
    for i, (a, b) in enumerate(zip(original.packets, packets)):
        assert a.tag == b.tag and len(a.payload) == len(b.payload)
        if i not in allowed:
            assert a == b
    assert source.to_bytes() == original_bytes
    for slot, values in ((2, replacement), (1, replacement[:-1]), (1, replacement.astype(float))):
        with pytest.raises(ValueError):
            replace_owner_codes(original, slot, values)
    chunks = list(original.packets)
    first = min(allowed)
    chunks[first] = replace(chunks[first], payload=b"\x01" + chunks[first].payload[1:])
    malformed = replace(original, packets=tuple(chunks))
    with pytest.raises(ValueError):
        replace_owner_codes(malformed, 1, replacement)


@pytest.mark.capture
def test_genuine_sample_replacement_recapture_has_exact_codes_and_preserved_headers():
    import hashlib

    from po33_re.artifacts import sha256_file
    from po33_re.modem.decode import decode_wav

    root = Path(__file__).resolve().parents[1]
    capture = root / "experiments/edited-sample-001/capture.wav"
    baseline = root / "experiments/edited-trim-001/capture.wav"
    if not capture.exists() or not baseline.exists():
        pytest.skip("Sample replacement recapture and prior trim WAV required")
    assert (
        sha256_file(capture) == "94b9b95f3468f4781d52542756cb858479a2a4cd3969826ad31658479919312d"
    )
    original = decode_artifact(decode_wav(baseline, 0.0063))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    assert hashlib.sha256(actual.encoded_body).hexdigest() == (
        "8f851166868fd99e7935a5942a2b82181f0268c3a05303f08852a0f06ebb30a0"
    )
    codes = sound_data(actual, 0)[9:]
    assert hashlib.sha256(codes).hexdigest() == (
        "80b1182143cb5ed850776979536137c650370ad2f31a8dfb4c14f357af89762d"
    )
    assert len(actual.packets) == len(original.packets) == 511
    allowed = set(sound_groups(original)[0])
    for i, (a, b) in enumerate(zip(original.packets, actual.packets)):
        assert a.tag == b.tag and len(a.payload) == len(b.payload)
        if i not in allowed:
            assert a == b
    for slot in (1, 2, 3, 8):
        assert sound_data(actual, slot - 1)[:9] == sound_data(original, slot - 1)[:9]
    audio = decode_signed_mulaw(np.frombuffer(codes[:46875], dtype=np.uint8))
    peak_bin = int(np.argmax(abs(np.fft.rfft(audio))))
    assert peak_bin * 23437.5 / len(audio) == 750
    assert 0.24 < abs(audio).max() < 0.26
