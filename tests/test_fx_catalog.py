import io

import numpy as np
import soundfile as sf

from scripts.check_fx_catalog_observation import control_plain, step_times, summarize
from scripts.fx_descriptor_method import SETTINGS, describe
from scripts.prepare_fx_catalog_observation import CYCLES, EFFECTS, FX_OF_STEP, WINDOWS_MS

RATE = 44100


def tone(seconds, hz, level=0.3):
    t = np.arange(int(seconds * RATE)) / RATE
    return level * np.sin(2 * np.pi * hz * t)


def test_effects_cover_1_to_15_once_each_with_one_control():
    assert sorted(FX_OF_STEP.values()) == list(range(1, 16))
    assert EFFECTS[3][14] is None and all(e is None for e in EFFECTS[2][1::2])


def test_descriptor_sees_a_plain_note_and_a_stutter(tmp_path):
    mono = np.zeros(int(3 * RATE))
    plain = int(0.5 * RATE)
    mono[plain : plain + len(tone(0.2, 784))] += tone(0.2, 784)
    stutter = int(1.5 * RATE)
    for k in range(4):
        s = stutter + int(k * 0.06 * RATE)
        mono[s : s + len(tone(0.04, 784))] += tone(0.04, 784)
    path = tmp_path / "p.wav"
    buffer = io.BytesIO()
    sf.write(buffer, np.column_stack((mono, mono)), RATE, subtype="FLOAT", format="WAV")
    path.write_bytes(buffer.getvalue())
    described = describe(path, [0.5, 1.5], WINDOWS_MS, 0, SETTINGS)
    assert control_plain(described[0])
    assert len(described[1]["onsets_ms"]) == 4
    keys = [(0, 0), (0, 5)]
    table = summarize(keys, described)
    assert table[0]["control_plain_in_every_cycle"] and table[5]["onset_counts"] == [4]


def test_step_times_follow_the_chain():
    keys, times = step_times(1.0, CYCLES)
    assert len(keys) == CYCLES * 16
    assert (
        times[keys.index((0, 1))] == 1.0
        and abs(times[keys.index((0, 9))] - (1.0 + 16 * 0.25)) < 1e-9
    )
    assert abs(times[keys.index((1, 0))] - (1.0 + 32 * 0.25 + 16 * 0.25 + 14 * 0.25)) < 1e-9
