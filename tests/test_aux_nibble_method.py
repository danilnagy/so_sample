"""The aux-nibble method classifies synthetic playbacks of both hypotheses correctly."""

import numpy as np
import pytest

from scripts.aux_nibble_method import SETTINGS, decide, measure
from scripts.prepare_aux_nibble_test import PREDICTIONS, TONE_SECONDS

RATE = 44100
STEP = SETTINGS["step_seconds"]
DRUM = [
    {"pattern": 1, "step": 1, "nibble": 1},
    {"pattern": 1, "step": 9, "nibble": 2},
    {"pattern": 2, "step": 1, "nibble": 3},
    {"pattern": 2, "step": 9, "nibble": 4},
    {"pattern": 3, "step": 1, "nibble": 6},
    {"pattern": 3, "step": 9, "nibble": 8},
    {"pattern": 4, "step": 1, "nibble": 5},
    {"pattern": 4, "step": 9, "nibble": 7},
]
MELODIC = [{"pattern": 5 + i, "step": 1, "nibble": n} for i, n in enumerate([0xF, 1, 2, 4, 8, 0xE])]


def synthetic(retrigger, length, lead=1.3, passes=2, drift=1.0002):
    """A stereo playback: clicks repeated `retrigger(n)` times in their step, tones `length(n)` long."""
    cycle = SETTINGS["chain_patterns"] * SETTINGS["steps_per_pattern"] * STEP
    total = lead + passes * cycle * drift + 2
    x = np.random.default_rng(1).normal(0, 0.002, int(total * RATE))
    click = 0.8 * np.sin(2 * np.pi * 3000 * np.arange(int(0.012 * RATE)) / RATE) * np.exp(-np.arange(int(0.012 * RATE)) / (0.004 * RATE))
    for p in range(passes):
        t0 = lead + p * cycle * drift
        for probe in DRUM:
            at = t0 + ((probe["pattern"] - 1) * 16 + probe["step"] - 1) * STEP * drift
            n = retrigger(probe["nibble"])
            for k in range(n):
                i = int((at + k * STEP / n) * RATE)
                x[i : i + len(click)] += click
        for probe in MELODIC:
            at = t0 + (probe["pattern"] - 1) * 16 * STEP * drift
            seconds = length(probe["nibble"])
            t = np.arange(int(seconds * RATE)) / RATE
            i = int(at * RATE)
            x[i : i + len(t)] += 0.6 * np.sin(2 * np.pi * 500 * t)
    return np.column_stack([x, x])


def classify(samples):
    measured = measure(samples, RATE, DRUM, MELODIC, TONE_SECONDS)
    return measured, decide(measured, PREDICTIONS)["predictions"]


def test_retrigger_and_length_are_recognised():
    counts = {1: 1, 2: 2, 3: 3, 4: 4, 6: 6, 8: 8, 5: 5, 7: 7}
    measured, result = classify(synthetic(lambda n: counts[n], lambda n: min(TONE_SECONDS, n * STEP)))
    assert len(measured["passes"]) == 2
    assert result["H1_drum_retrigger"]["holds"] and not result["H0_drum_no_effect"]["holds"]
    assert result["H1_melodic_length"]["holds"] and not result["H0_melodic_no_effect"]["holds"]


def test_no_effect_is_recognised():
    _, result = classify(synthetic(lambda n: 1, lambda n: TONE_SECONDS))
    assert result["H0_drum_no_effect"]["holds"] and not result["H1_drum_retrigger"]["holds"]
    assert result["H0_melodic_no_effect"]["holds"] and not result["H1_melodic_length"]["holds"]


def test_a_different_rule_fails_both():
    # Repeats at half the count, and lengths in half steps: neither hypothesis holds.
    _, result = classify(synthetic(lambda n: max(1, n // 2) if n > 1 else 2, lambda n: min(TONE_SECONDS, n * STEP / 2)))
    assert not result["H1_drum_retrigger"]["holds"] and not result["H0_drum_no_effect"]["holds"]
    assert not result["H1_melodic_length"]["holds"] and not result["H0_melodic_no_effect"]["holds"]


def test_no_clicks_is_an_error():
    with pytest.raises(ValueError):
        measure(np.zeros((RATE * 5, 2)), RATE, DRUM, MELODIC, TONE_SECONDS)
