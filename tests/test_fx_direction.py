import io

import numpy as np
import soundfile as sf

from scripts.check_fx_direction_test import classify, matches, sequence
from scripts.fx_direction_method import SEGMENT_HZ, SETTINGS, describe_notes, nearest_segment
from scripts.prepare_fx_direction_test import HELD, MODELS, effects_for, keys

RATE = 44100


def note(order):
    out = []
    for k in order:
        t = np.arange(int(0.1667 * RATE)) / RATE
        out.append(0.3 * np.sin(2 * np.pi * SEGMENT_HZ[k - 1] * t))
    return np.concatenate(out)


def wav(tmp_path, orders):
    mono = np.zeros(int((1 + len(orders)) * RATE))
    for i, order in enumerate(orders):
        start = int((0.5 + i) * RATE)
        n = note(order)
        mono[start : start + len(n)] += n
    path = tmp_path / "p.wav"
    buffer = io.BytesIO()
    sf.write(buffer, np.column_stack((mono, mono)), RATE, subtype="FLOAT", format="WAV")
    path.write_bytes(buffer.getvalue())
    return path


def test_segments_are_read_in_order(tmp_path):
    path = wav(tmp_path, [[1, 2, 3, 4], [4, 3, 2, 1], [1, 1, 1, 1]])
    notes = describe_notes(path, [0.5, 1.5, 2.5], 0, SETTINGS)
    assert sequence(notes[0]) == [1, 2, 3, 4, None]
    assert sequence(notes[1]) == [4, 3, 2, 1, None]
    assert matches(sequence(notes[2]), MODELS["hold_first"])
    assert classify([notes[1]] * 3) == "reverse" and classify([notes[0]] * 3) == "forward"
    assert classify([notes[0], notes[1], notes[2]]) == "described"
    assert nearest_segment(SEGMENT_HZ[2] * 1.01)[0] == 3


def test_plan_layout():
    assert keys() == [1, None, None, None] * 4
    assert effects_for(9) == [None] * 16 and effects_for(3)[4:] == [15] * 12 and HELD[3] == 15
