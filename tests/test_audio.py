import hashlib

import numpy as np
import pytest
import soundfile as sf

from po33_re.audio import inspect_wav


@pytest.mark.parametrize("rate", [44100, 48000])
@pytest.mark.parametrize("subtype", ["PCM_U8", "PCM_16", "PCM_24", "PCM_32"])
def test_pcm_widths_rates_and_statistics(tmp_path, rate, subtype):
    path = tmp_path / "capture.wav"
    sf.write(path, np.tile([0.5, -0.25], (100, 1)), rate, subtype=subtype)
    before = path.read_bytes()
    report = inspect_wav(path)
    assert report["frames"] == 100
    assert report["sample_rate_hz"] == rate
    assert report["pcm_subtype"] == subtype
    assert report["duration_seconds"] == 100 / rate
    assert report["source_sha256"] == hashlib.sha256(before).hexdigest()
    assert report["channels"]["left"]["rms"] == 0.5
    assert report["channels"]["right"]["peak_amplitude"] == 0.25
    assert report["channel_similarity"]["correlation"] is None
    assert report["channel_similarity"]["identical"] is False
    assert path.read_bytes() == before


@pytest.mark.parametrize("channels", [1, 3])
def test_reject_channel_count(tmp_path, channels):
    path = tmp_path / "bad.wav"
    sf.write(path, np.zeros((10, channels)), 48000, subtype="PCM_16")
    with pytest.raises(ValueError, match="2 stereo channels"):
        inspect_wav(path)


@pytest.mark.parametrize("subtype", ["FLOAT", "DOUBLE", "ULAW"])
def test_reject_encoding(tmp_path, subtype):
    path = tmp_path / "bad.wav"
    sf.write(path, np.zeros((10, 2)), 48000, subtype=subtype)
    with pytest.raises(ValueError, match="integer PCM"):
        inspect_wav(path)


def test_empty_and_malformed(tmp_path):
    path = tmp_path / "bad.wav"
    sf.write(path, np.zeros((0, 2)), 48000, subtype="PCM_16")
    with pytest.raises(ValueError, match="Empty"):
        inspect_wav(path)
    path.write_bytes(b"not a WAV")
    with pytest.raises(ValueError, match="Invalid WAV"):
        inspect_wav(path)


def test_clipping_and_duplicate_channels(tmp_path):
    path = tmp_path / "clip.wav"
    sf.write(path, np.array([[-1, -1], [0, 0], [1, 1]], dtype=float), 48000, subtype="PCM_16")
    report = inspect_wav(path)
    assert report["channels"]["left"]["near_full_scale_samples"] == 2
    assert report["channel_similarity"]["identical"] is True
    assert report["channel_similarity"]["correlation"] == pytest.approx(1)


def test_truncated_pcm_data(tmp_path):
    path = tmp_path / "truncated.wav"
    sf.write(path, np.zeros((100, 2)), 48000, subtype="PCM_16")
    path.write_bytes(path.read_bytes()[:-40])
    with pytest.raises(ValueError, match="Truncated"):
        inspect_wav(path)
