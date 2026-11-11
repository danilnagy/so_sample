import io
import math

import numpy as np
import soundfile as sf

from scripts.fx_period_method import SETTINGS, period_ms, pitch_track
from scripts.prepare_fx_period_test import CANDIDATES, classify

RATE = 44100
SEGMENTS = [400.0 * 2 ** (7 / 12) * k / 4 for k in (4, 5, 6, 7)]


def looping_note(period_s, seconds=1.4):
    out = np.zeros(int(seconds * RATE))
    t = 0.0
    while t < seconds:
        for k, hz in enumerate(SEGMENTS):
            a, b = t + k * 0.1667, t + (k + 1) * 0.1667
            a_i, b_i = int(a * RATE), min(int(b * RATE), int(min(t + period_s, seconds) * RATE))
            if b_i > a_i:
                tt = np.arange(b_i - a_i) / RATE
                out[a_i:b_i] += 0.3 * np.sin(2 * np.pi * hz * tt)
        t += period_s
    return out


def wav(tmp_path, notes):
    mono = np.zeros(int((1 + 2 * len(notes)) * RATE))
    for i, n in enumerate(notes):
        start = int((0.5 + 2 * i) * RATE)
        mono[start : start + len(n)] += n
    path = tmp_path / "p.wav"
    buffer = io.BytesIO()
    sf.write(buffer, np.column_stack((mono, mono)), RATE, subtype="FLOAT", format="WAV")
    path.write_bytes(buffer.getvalue())
    return path


def test_periods_are_recovered(tmp_path):
    plain = looping_note(10.0, seconds=0.667)
    path = wav(tmp_path, [plain, looping_note(0.25), looping_note(0.3333), looping_note(0.125)])
    tracks = pitch_track(path, [0.5, 2.5, 4.5, 6.5], SETTINGS)
    assert period_ms(tracks[0], SETTINGS)[0] is None
    for track, expected in zip(tracks[1:], (250, 333, 125), strict=True):
        measured, _ = period_ms(track, SETTINGS)
        assert measured is not None and abs(measured - expected) <= 0.08 * expected


def test_candidate_classification():
    assert classify(250.0) == "1/16" and classify(340.0) == "1/12" and classify(62.0) == "1/64"
    assert classify(200.0) == "unresolved" and classify(None) == "unresolved"
    assert math.isclose(CANDIDATES["1/8"], 500.0)
