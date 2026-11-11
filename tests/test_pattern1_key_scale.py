import numpy as np
import pytest
import soundfile as sf
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.formats.packets import decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data
from scripts.pattern1_key_scale_method import MODELS, SETTINGS, decide, intervals, step_frequencies
from scripts.prepare_pattern1_key_scale_map import scale_checks, scale_pattern

RATE = 44100
BASE = 1190.417
SIXTEEN = pattern_bytes([(s, 3, "0e0981", 0xF0) for s in range(1, 17)])


def write_scale(path, cents, loops=6):
    """Each step plays the base tone transposed by cents, shortened like a faster sample."""
    step = round(0.25 * RATE)
    loop = np.zeros(16 * step)
    for s, c in enumerate(cents, 1):
        ratio = 2 ** (c / 1200)
        t = np.arange(round(0.21 / ratio * RATE)) / RATE
        tone = 0.3 * np.sin(2 * np.pi * BASE * ratio * t)
        loop[(s - 1) * step : (s - 1) * step + len(tone)] += tone
    mono = np.r_[np.zeros(RATE), np.tile(loop, loops)]
    sf.write(path, np.column_stack((mono, mono)), RATE, subtype="PCM_16")


@pytest.mark.parametrize("model", ["chromatic", "major", "natural_minor"])
def test_each_registered_scale_is_recognised(tmp_path, model):
    write_scale(tmp_path / "s.wav", MODELS[model])
    tracks, steps = step_frequencies(tmp_path / "s.wav", SETTINGS)
    assert tracks["missing_grid_positions"] == []
    table = intervals(steps)
    assert abs(table["step1_hz"] - BASE) < 1.0
    errors = [abs(table["steps"][s]["median_cents"] - MODELS[model][s - 1]) for s in range(1, 17)]
    assert max(errors) < 5
    assert decide(table)["classification"] == model


def test_an_unregistered_scale_is_reported_not_forced(tmp_path):
    cents = [0, 150, 300, 450, 600, 750, 900, 1050, 1200, 1350, 1500, 1650, 1800, 1950, 2100, 2250]
    write_scale(tmp_path / "s.wav", cents)
    table = intervals(step_frequencies(tmp_path / "s.wav", SETTINGS)[1])
    assert decide(table)["classification"] == "other_or_inconclusive"
    assert abs(table["steps"][4]["median_cents"] - 450) < 5


def test_scale_pattern_sets_keys_and_clears_effects():
    data = scale_pattern(SIXTEEN[:1024] + bytes.fromhex("6ff6ff666ff6ff66"))
    assert [data[768 + 16 * (s - 1) + 2] for s in range(1, 17)] == [0xF0 | k for k in range(16)]
    assert data[1024:] == b"\xff" * 8
    base = decode_frame(encode_packets(synthetic_packets(patterns={1: SIXTEEN})), start=0)
    actual = decode_frame(encode_packets(_replace_pattern_data(base, 1, data)), start=0)
    assert all(scale_checks(base, actual).values())


def test_scale_pattern_requires_the_calibrated_notes():
    with pytest.raises(ValueError, match="calibrated Sound3"):
        scale_pattern(pattern_bytes([(1, 3, "0e0981", 0xF0)]))
