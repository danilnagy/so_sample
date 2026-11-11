import io

import numpy as np
import pytest
import soundfile as sf
from test_drum_import import empty_frame

from po33_re.sample_import import (
    DEVICE_SAMPLE_LIMIT,
    import_melodic_sample_packets,
    prepare_pcm_sample,
)
from scripts.long_note_method import SETTINGS, decide, measure
from scripts.prepare_long_melodic_test import (
    CAPACITY,
    EXPECTED_HZ,
    EXPECTED_MS,
    NATIVE_CODES,
    TOTAL,
    sample_wav,
)


def test_sample_converts_to_the_planned_length():
    native, _ = prepare_pcm_sample(sample_wav(), None, (2344, NATIVE_CODES))
    assert len(native) == NATIVE_CODES and -(-NATIVE_CODES // 4096) * 4096 == CAPACITY
    assert TOTAL == 872448 <= DEVICE_SAMPLE_LIMIT


def test_page_capacity_is_opt_in():
    frame = empty_frame()
    long = np.zeros(NATIVE_CODES)
    with pytest.raises(ValueError, match="frames"):
        import_melodic_sample_packets(frame, 6, long, None, (6,), DEVICE_SAMPLE_LIMIT)
    _, allocation = import_melodic_sample_packets(
        frame, 6, long, None, (6,), DEVICE_SAMPLE_LIMIT, NATIVE_CODES, True
    )
    assert allocation["capacity_codes"] == CAPACITY and allocation["endpoint"] == NATIVE_CODES
    with pytest.raises(ValueError, match="pages"):
        import_melodic_sample_packets(
            frame, 6, long, 94000, (6,), DEVICE_SAMPLE_LIMIT, NATIVE_CODES, True
        )


def synthetic_playback(tmp_path, duration_s):
    rate = 44100
    out = np.zeros(int(22 * rate))
    for loop in range(5):
        start = int((0.5 + 4.0 * loop) * rate)
        n = int(duration_s * rate)
        t = np.arange(n) / rate
        quarter = n // 4
        freq = np.repeat(EXPECTED_HZ, quarter + 1)[:n]
        phase = 2 * np.pi * np.cumsum(freq) / rate
        out[start : start + n] = 0.3 * np.sin(phase) * (t >= 0)
    path = tmp_path / "playback.wav"
    buffer = io.BytesIO()
    sf.write(buffer, np.column_stack((out, out)), rate, subtype="PCM_16", format="WAV")
    path.write_bytes(buffer.getvalue())
    return path


def test_method_recognises_the_whole_sample(tmp_path):
    _, loops = measure(synthetic_playback(tmp_path, EXPECTED_MS / 1000), SETTINGS)
    result = decide(loops, EXPECTED_MS, EXPECTED_HZ, SETTINGS)
    assert result["duration_holds"] and result["pitch_holds"]


def test_method_rejects_a_truncated_note(tmp_path):
    _, loops = measure(synthetic_playback(tmp_path, 0.88), SETTINGS)
    assert not decide(loops, EXPECTED_MS, EXPECTED_HZ, SETTINGS)["duration_holds"]
