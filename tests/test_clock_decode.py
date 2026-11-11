import hashlib
from pathlib import Path

import numpy as np
import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, rebuild_labels
from po33_re.modem.clock_decode import decode_clock_wav, recover_channel
from po33_re.modem.encode import encode_artifact
from po33_re.modem.symbols import load_artifact


@pytest.mark.parametrize("rate", [44100, 48000])
def test_measured_clock_recovers_waveform_not_corrupted_reference_payload(rate):
    rng = np.random.default_rng(89)
    oracle = rng.integers(0, 4, 12000, dtype=np.uint8)
    n = np.arange(round(10000 * rate / 7812.5))
    t = n * 7812.7 / rate + 0.037
    i = 2 * (oracle[np.floor(t + 0.625).astype(int)] >> 1).astype(float) - 1
    q = 2 * (oracle[np.floor(t - 0.125).astype(int).clip(0)] & 1).astype(float) - 1
    signal = 0.35 * (i * np.cos(2 * np.pi * (t - 0.125)) + q * np.sin(2 * np.pi * (t - 0.125)))
    reference = oracle.copy()
    reference[3000:] ^= 1  # Correct pre-frame acquisition, intentionally wrong later labels.
    recovered, report = recover_channel(signal, rate, reference)
    assert np.array_equal(recovered, oracle[: len(recovered)])
    assert report["alignment"]["payload_used_for_alignment"] is False
    assert report["quarter_mismatches"] == [0, 0, 0, 0]
    assert report["first_original_crossing_mismatch"] == 3000


def test_measured_clock_fails_closed_without_unique_preamble_or_signal():
    with pytest.raises(ValueError):
        recover_channel(np.zeros(4000), 44100, np.zeros(3000, dtype=np.uint8))
    with pytest.raises(ValueError):
        recover_channel(np.zeros(4000), 44100, np.zeros(100, dtype=np.uint8))


@pytest.mark.capture
def test_genuine_timing_slip_recovers_all_packets_and_preserves_failed_source():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-note-key-001"
    path = directory / "capture.wav"
    source_path = directory / "derived/analysis-001/capture.symbols.npz"
    target_path = root / "experiments/generated-note-key-001/edited.symbols.npz"
    if not all(p.is_file() for p in (path, source_path, target_path)):
        pytest.skip(
            "Timing-slip recapture, original crossing artifact and software target required"
        )
    assert sha256_file(path) == "c5add754a44ac012a44114156839349f64024c6a2f69660571dbb5b1d59c67ed"
    acquisition = load_artifact(source_path)
    unchanged = acquisition.to_bytes()
    with pytest.raises(ValueError, match="wire byte13130"):
        decode_artifact(acquisition)
    recovered, report = decode_clock_wav(path, acquisition)
    frame, target = decode_artifact(recovered), decode_artifact(load_artifact(target_path))
    assert len(frame.packets) == 511 and frame.end_byte == 89396
    assert hashlib.sha256(frame.encoded_body).hexdigest() == (
        "91b37d61e3bc71de72748dfd846892e62a7d839a9332f13a6f9c56687cdeadf0"
    )
    assert frame.encoded_body == target.encoded_body and frame.packets == target.packets
    assert acquisition.to_bytes() == unchanged
    assert report["target_data_used"] is False
    assert report["channels"]["left"]["first_original_crossing_mismatch"] == 26472
    for ch in ("left", "right"):
        assert report["channels"][ch]["quarter_mismatches"] == [0, 0, 0, 0]
    with pytest.raises(ValueError, match="unobserved capture edges"):
        encode_artifact(recovered)
    canonical = rebuild_labels(recovered, frame.packets)
    assert canonical.metadata.get("transport_extent") is None
    assert decode_artifact(canonical).encoded_body == frame.encoded_body
    encode_artifact(canonical)


@pytest.mark.capture
def test_clock_rejects_wrong_acquisition_source_identity():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/edited-note-key-001/capture.wav"
    acquisition_path = (
        root / "experiments/event-008-b-melodic-key2/derived/analysis-001/capture.symbols.npz"
    )
    if not path.exists() or not acquisition_path.exists():
        pytest.skip("Two distinct genuine recordings required")
    with pytest.raises(ValueError, match="does not match"):
        decode_clock_wav(path, load_artifact(acquisition_path))
