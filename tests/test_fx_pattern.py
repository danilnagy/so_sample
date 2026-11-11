import io

import numpy as np
import soundfile as sf

from scripts.check_fx_pattern_observation import control_run, nearest_key, table
from scripts.fx_pattern_method import SETTINGS, describe_steps
from scripts.prepare_fx_pattern_observation import CHAIN, KEY_HZ, effects_for

RATE = 44100


def run_wav(path, reverse_steps=()):
    mono = np.zeros(int(6 * RATE))
    for step in range(16):
        key = 15 - step if step in reverse_steps else step
        start = int((0.5 + step * 0.25) * RATE)
        t = np.arange(int(0.2 * RATE)) / RATE
        mono[start : start + len(t)] += 0.3 * np.sin(2 * np.pi * KEY_HZ[key] * t)
    buffer = io.BytesIO()
    sf.write(buffer, np.column_stack((mono, mono)), RATE, subtype="FLOAT", format="WAV")
    path.write_bytes(buffer.getvalue())


def test_control_run_and_key_mapping(tmp_path):
    path = tmp_path / "run.wav"
    run_wav(path)
    described = describe_steps(path, [0.5], (0, 1), SETTINGS)
    assert control_run(described[0])
    assert nearest_key(KEY_HZ[12] * 1.005)[0] == 13
    rows = table([described[0]] * len(CHAIN))
    assert [r["windows"][0]["key"] for r in rows[16]] == list(range(1, 17))


def test_reversed_steps_are_seen(tmp_path):
    path = tmp_path / "rev.wav"
    run_wav(path, reverse_steps=range(4, 12))
    described = describe_steps(path, [0.5], (0, 1), SETTINGS)
    assert not control_run(described[0])
    keys = [nearest_key(s["windows"][0]["hz"])[0] for s in described[0]]
    assert keys[4:12] == list(range(12, 4, -1))


def test_effect_placement():
    assert effects_for(16) == [None] * 16
    assert effects_for(3) == [None] * 4 + [3] * 8 + [None] * 4
