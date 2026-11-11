"""The aux-nibble-003 method tells the registered tempo and swing hypotheses apart on synthetic playbacks."""

import json
from pathlib import Path

import numpy as np
import pytest

from scripts.aux_nibble3_method import SETTINGS, decide, measure
from scripts.prepare_aux_nibble_3_test import DIRECTORY, PREDICTIONS

RATE = 44100
STEP = SETTINGS["step_seconds"]
DELAY = SETTINGS["swing_delay_seconds"]
PROJECT = Path(__file__).resolve().parents[1] / "experiments" / DIRECTORY / "project.json"
pytestmark = pytest.mark.skipif(not PROJECT.exists(), reason="aux-nibble-003 not built")


def layout():
    project = json.loads(PROJECT.read_text())
    return project["drum_probes"], project["melodic_probes"]


def synthetic(spacing, length, passes=4, lead=1.1, drift=1.0002):
    """spacing(n, parity) and length(n, parity) in seconds, parity 'o' or 'e'."""
    drums, mels = layout()
    cycle = SETTINGS["chain_patterns"] * 16 * STEP
    x = np.random.default_rng(3).normal(0, 0.001, int((lead + passes * cycle * drift + 2) * RATE))
    tc = np.arange(int(0.006 * RATE)) / RATE
    click = 0.8 * np.sin(2 * np.pi * 5000 * tc) * np.exp(-tc / 0.0012)
    for k in range(passes):
        t0 = lead + k * cycle * drift

        def start(p, t0=t0):
            grid = t0 + ((p["pattern"] - 1) * 16 + p["step"] - 1) * STEP * drift
            return grid + (DELAY * drift if p["step"] % 2 == 0 else 0.0)

        for p in drums:
            parity = "e" if p["step"] % 2 == 0 else "o"
            for r in range(p["nibble"]):
                i = int((start(p) + r * spacing(p["nibble"], parity) * drift) * RATE)
                x[i : i + len(click)] += click
        for p in mels:
            parity = "e" if p["step"] % 2 == 0 else "o"
            t = np.arange(int(length(p["nibble"], parity) * RATE)) / RATE
            i = int(start(p) * RATE)
            hz = 1000 if p["step"] % 2 == 0 else 700
            x[i : i + len(t)] += 0.5 * np.sin(2 * np.pi * hz * t)
    return np.column_stack([x, x])


def held(samples):
    drums, mels = layout()
    measured = measure(samples, RATE, drums, mels)
    result = decide(measured, PREDICTIONS)
    return measured, {k for k, v in result["predictions"].items() if v["holds"]}


def grid_end(n, parity):
    return n * STEP if n % 2 == 0 else n * STEP + (DELAY if parity == "o" else -DELAY)


def test_scaling_with_the_step():
    measured, h = held(synthetic(lambda n, p: STEP / n, lambda n, p: n * STEP))
    assert len(measured["passes"]) == 4
    assert h == {"H_spacing_scales_with_step", "H_length_scales_with_step"}


def test_spanning_the_swung_step_and_ending_on_the_swung_grid():
    _, h = held(synthetic(lambda n, p: ((STEP + DELAY) if p == "o" else (STEP - DELAY)) / n, grid_end))
    assert h == {"H_spacing_spans_swung_step", "H_length_ends_on_swung_grid"}


def test_fixed_time():
    _, h = held(synthetic(lambda n, p: 0.25 / n, lambda n, p: n * 0.25))
    assert h == {"H_spacing_fixed_time", "H_length_fixed_time"}


def test_another_rule_fails_all():
    _, h = held(synthetic(lambda n, p: 0.09 / n + 0.004, lambda n, p: n * STEP * 1.5))
    assert h == set()


def test_silence_is_an_error():
    drums, mels = layout()
    with pytest.raises(ValueError):
        measure(np.zeros((RATE * 5, 2)), RATE, drums, mels)
