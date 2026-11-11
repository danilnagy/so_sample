import io

import numpy as np
import soundfile as sf

from scripts.check_polyphony_test import evaluate
from scripts.polyphony_method import SETTINGS, presence, voice_levels
from scripts.prepare_polyphony_test import (
    SOLO_STEPS,
    SOUND_ORDER,
    STACKS,
    VOICES,
    keys_for,
)

RATE = 44100


def synthetic(path, limit):
    mono = np.zeros(int(17.5 * RATE))
    length = int(0.3 * RATE)
    t = np.arange(length) / RATE
    for cycle in range(2):
        for step in range(1, 33):
            if step <= 16:
                sounds = [s for s, st in SOLO_STEPS.items() if st == step]
            else:
                sounds = STACKS.get(step - 16, [])[:limit]
            start = int((0.5 + (cycle * 32 + step - 1) * 0.25) * RATE)
            for s in sounds:
                mono[start : start + length] += 0.05 * np.sin(2 * np.pi * VOICES[s] * t)
    buffer = io.BytesIO()
    sf.write(buffer, np.column_stack((mono, mono)), RATE, subtype="FLOAT", format="WAV")
    path.write_bytes(buffer.getvalue())


def run(tmp_path, limit):
    path = tmp_path / f"playback{limit}.wav"
    synthetic(path, limit)
    frequencies = [VOICES[s] for s in SOUND_ORDER]
    _, levels = voice_levels(path, 64, frequencies, SETTINGS)
    solo = {SOUND_ORDER.index(s): step for s, step in SOLO_STEPS.items()}
    cycles = presence(levels, solo, [16 + s for s in STACKS], 32, SETTINGS)
    return evaluate(cycles)


def test_all_voices_present_classifies_as_limit_14(tmp_path):
    result = run(tmp_path, 14)
    assert result["classification"] == "voice_limit_14"
    assert result["stacks"]["11"]["count"] == 14 and result["stacks"]["15"]["count"] == 6


def test_dropping_voices_classifies_the_limit(tmp_path):
    assert run(tmp_path, 6)["classification"] == "voice_limit_6"


def test_plan_shapes():
    assert len(VOICES) == 14 and len({round(v) for v in VOICES.values()}) == 14
    assert keys_for(2, 13)[8] == 1 and keys_for(3, 16)[14] == 1 and keys_for(3, 1)[0] == 1
