import io

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

from scripts.check_filter_law_test import evaluate, per_code
from scripts.filter_response_method import SETTINGS, harmonic_amplitudes, responses
from scripts.prepare_filter_law_test import FILTER_CODES, saw_wav, step_codes

RATE = 44100


def saw(seconds):
    t = np.arange(round(seconds * RATE)) / RATE
    return sum(np.sin(2 * np.pi * h * 200 * t) / h for h in range(1, 56)) * 0.05


def write(path, steps):
    out = [np.zeros(RATE // 2)]
    for kind, cutoff in steps:
        tone = saw(0.25)
        if kind == "lp":
            tone = sosfilt(butter(4, cutoff, "low", fs=RATE, output="sos"), tone)
        elif kind == "hp":
            tone = sosfilt(butter(4, cutoff, "high", fs=RATE, output="sos"), tone)
        out.append(tone)
    out.append(np.zeros(RATE // 2))
    mono = np.concatenate(out)
    buffer = io.BytesIO()
    sf.write(buffer, np.column_stack((mono, mono)), RATE, subtype="FLOAT", format="WAV")
    path.write_bytes(buffer.getvalue())


def test_method_recovers_types_and_rising_edges(tmp_path):
    codes = [63, 10, 20, 63, 40, 50]
    steps = [("by", 0), ("lp", 1000), ("lp", 3000), ("by", 0), ("hp", 1000), ("hp", 3000)]
    path = tmp_path / "playback.wav"
    write(path, steps)
    _, amplitudes = harmonic_amplitudes(path, len(codes), SETTINGS)
    response = responses(amplitudes, codes, len(codes))
    table = per_code(response, codes)
    assert [table[c]["type"] for c in (10, 20, 40, 50)] == ["low_pass"] * 2 + ["high_pass"] * 2
    assert table[10]["edge_hz"] < table[20]["edge_hz"]
    assert table[40]["edge_hz"] < table[50]["edge_hz"]
    result = evaluate(response, codes, table)
    assert result["hypotheses"]["reference_consistent"]
    assert result["hypotheses"]["edges_monotonic"]


def test_plan_covers_every_code():
    codes = set(step_codes())
    assert codes == set(range(64)) and len(step_codes()) == 80
    assert all(FILTER_CODES[p][0] == 63 for p in FILTER_CODES)
    samples, rate = sf.read(io.BytesIO(saw_wav()))
    assert rate == 48000 and len(samples) == 13056 and np.abs(samples).max() <= 0.51
