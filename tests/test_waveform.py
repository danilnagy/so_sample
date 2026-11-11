import numpy as np
import pytest

from po33_re.analysis.waveform import amplitude_clock, sample_quarters


@pytest.mark.parametrize("rate", [44100, 48000])
def test_amplitude_clock_independent_known_quarter_signs(rate):
    rng = np.random.default_rng(89)
    labels = rng.integers(0, 4, 12000, dtype=np.uint8)
    n = np.arange(round(10000 * rate / 7812.5))
    phase_offset = 0.037
    # Independent analytic I/Q waveform, including a small carrier frequency offset.
    t = n * 7812.7 / rate + phase_offset
    i = 2 * (labels[np.floor(t + 0.625).astype(int)] >> 1).astype(float) - 1
    q = 2 * (labels[np.floor(t - 0.125).astype(int).clip(0)] & 1).astype(float) - 1
    signal = 0.35 * (i * np.cos(2 * np.pi * (t - 0.125)) + q * np.sin(2 * np.pi * (t - 0.125)))
    centers, correction, _ = amplitude_clock(signal, rate)
    oracle = centers * (7812.7 - 7812.5) / rate + phase_offset
    assert np.max(abs(correction - oracle)) < 0.003
    quarters, signs, _ = sample_quarters(signal, rate, centers, correction)
    cycle = (quarters + 0.5) / 4
    expected = np.where(
        quarters % 4 == 0,
        labels[np.floor(cycle).astype(int)] >> 1,
        np.where(
            quarters % 4 == 1,
            labels[np.floor(cycle).astype(int)] & 1,
            np.where(
                quarters % 4 == 2,
                1 - (labels[np.floor(cycle).astype(int) + 1] >> 1),
                1 - (labels[np.floor(cycle).astype(int)] & 1),
            ),
        ),
    )
    assert np.array_equal(signs, expected)


def test_amplitude_clock_rejects_silence_and_nonfinite_values():
    with pytest.raises(ValueError):
        amplitude_clock(np.zeros(3000), 44100)
    with pytest.raises(ValueError):
        amplitude_clock(np.full(3000, np.nan), 44100)
