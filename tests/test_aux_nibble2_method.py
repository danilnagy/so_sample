"""The aux-nibble-002 method tells the registered hypotheses apart on synthetic playbacks."""

import json
from pathlib import Path

import numpy as np
import pytest
from scipy.signal import butter, sosfiltfilt

from scripts.aux_nibble2_method import SETTINGS, decide, measure
from scripts.prepare_aux_nibble_2_test import DIRECTORY, MEL_SECONDS, PREDICTIONS, probes_from

RATE = 44100
STEP = SETTINGS["step_seconds"]
PROJECT = Path(__file__).resolve().parents[1] / "experiments" / DIRECTORY / "project.json"
pytestmark = pytest.mark.skipif(not PROJECT.exists(), reason="aux-nibble-002 not built")


def probes():
    return probes_from(json.loads(PROJECT.read_text()))


def strike():
    t = np.arange(int(1.0 * RATE)) / RATE
    noise = np.random.default_rng(5).normal(0, 1, len(t))
    body = sosfiltfilt(butter(2, [2400, 3600], btype="bandpass", fs=RATE, output="sos"), noise)
    body *= 0.3 / np.abs(body[: int(0.05 * RATE)]).max()
    return 0.5 * np.sin(2 * np.pi * 7000 * t) * np.exp(-t / 0.0012) + body * np.exp(-t / 0.35)


def synthetic(model, length, passes=2, lead=1.3, drift=1.0001):
    """model: 'restart' (one voice, each repeat cuts the last) or 'per_repeat' (a voice each, overlapping)."""
    p = probes()
    cycle = SETTINGS["chain_patterns"] * 16 * STEP
    x = np.random.default_rng(1).normal(0, 0.001, int((lead + passes * cycle * drift + 3) * RATE))
    hit = strike()
    at = lambda t0, q: t0 + ((q["pattern"] - 1) * 16 + q["step"] - 1) * STEP * drift

    def add(start, signal):
        i = int(start * RATE)
        x[i : i + len(signal)] += signal[: max(0, len(x) - i)]

    def tone(start, hz, seconds):
        t = np.arange(int(seconds * RATE)) / RATE
        add(start, 0.4 * np.sin(2 * np.pi * hz * t))

    for k in range(passes):
        t0 = lead + k * cycle * drift
        add(at(t0, p["reference"]), hit)
        for v in p["voice_probes"]:
            start = at(t0, v["probe"])
            if model == "restart":
                for r in range(4):
                    seg = hit if r == 3 else hit[: int(STEP / 4 * RATE)]
                    add(start + r * STEP / 4, seg)
            elif model == "per_repeat":
                for r in range(4 - v["held"]):
                    add(start + r * STEP / 4, hit)
            else:  # 'first_only': one hit whatever is held
                add(start, hit)
        for h in p["holder_probes"]:
            tone(at(t0, h), p["hz_by_sound"][str(h["sound"])], 2.0)
        for q in p["length_probes"]:
            tone(at(t0, q), p["hz_by_sound"][str(q["sound"])], length(q["nibble"]))
        for f in p["fx_patterns"]:
            if f["probe"]["sound"] == p["drum_sound"]:
                add(at(t0, f["probe"]), hit)
            else:
                tone(at(t0, f["probe"]), p["hz_by_sound"][str(f["probe"]["sound"])], 2 * STEP)
    return np.column_stack([x, x])


def judge(samples):
    measured = measure(samples, RATE, probes())
    return measured, decide(measured, PREDICTIONS)


def test_one_voice_restart_and_lengths_in_steps_with_f_as_fifteen():
    measured, result = judge(synthetic("restart", lambda n: n * STEP))
    held = {k for k, v in result["predictions"].items() if v["holds"]}
    assert len(measured["passes"]) == 2
    assert held == {"H1_one_voice", "H1_restart", "H_holders_continue", "H_length_steps", "H_F_15_steps"}, result


def test_a_voice_per_repeat_overlapping_and_f_as_the_whole_sample():
    _, result = judge(synthetic("per_repeat", lambda n: MEL_SECONDS if n == 0xF else n * STEP))
    held = {k for k, v in result["predictions"].items() if v["holds"]}
    assert held == {"H2_voice_per_repeat", "H2_overlap", "H_holders_continue", "H_length_steps", "H_F_whole_sample"}, result
    assert 3.0 <= result["overlap_predicted_db"] <= 5.5


def test_another_rule_fails_both_of_each_pair():
    _, result = judge(synthetic("first_only", lambda n: n * STEP / 2))
    held = {k for k, v in result["predictions"].items() if v["holds"]}
    assert held == {"H_holders_continue"}, result


def test_silence_is_an_error():
    with pytest.raises(ValueError):
        measure(np.zeros((RATE * 5, 2)), RATE, probes())
