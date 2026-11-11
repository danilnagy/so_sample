import numpy as np
import pytest

from po33_re.analysis.playback import measure_tone


@pytest.mark.parametrize("rate", [44100, 48000])
def test_known_playback_duration_frequency_and_noise(rate):
    rng = np.random.default_rng(95)
    values = rng.normal(0, 0.0003, 3 * rate)
    start, end = round(0.7 * rate), round(2.0 * rate)
    t = np.arange(end - start) / rate
    values[start:end] += 0.05 * np.sin(2 * np.pi * 563.27 * t) + 0.003 * np.sin(
        4 * np.pi * 563.27 * t
    )
    result = measure_tone(values, rate)
    assert abs(result["dominant_frequency_hz"] - 563.27) < 0.003
    assert result["audible_duration_seconds"] == pytest.approx(1.3, abs=0.01)
    assert result["audible_span_seconds"][0] == pytest.approx(0.7, abs=0.01)
    assert 0.99 < result["single_sine_explained_variance"] < 1


def test_playback_measurement_refuses_noise_only_and_nonfinite_audio():
    rng = np.random.default_rng(96)
    with pytest.raises(ValueError):
        measure_tone(rng.normal(0, 0.0003, 44100), 44100)
    with pytest.raises(ValueError):
        measure_tone(np.full(44100, np.nan), 44100)
