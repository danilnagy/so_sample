"""The audition-lock method on synthetic recordings of the three hit groups."""

import numpy as np
import pytest
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

from scripts.audition_lock_method import OUTCOMES, SETTINGS, analyze, groups_of

RATE = 44100


def saw(seconds=0.27, harmonics=55, f0=200.0):
    t = np.arange(round(seconds * RATE)) / RATE
    out = sum(np.sin(2 * np.pi * f0 * h * t) / h for h in range(1, harmonics + 1))
    return out / np.abs(out).max() * 0.5


def low_passed(hit, cutoff_hz=400.0):
    sos = butter(2, cutoff_hz, btype="low", fs=RATE, output="sos")
    return sosfiltfilt(sos, hit)


def recording(path, before, pattern, after):
    """Hits placed at the registered cadence: four by hand, eight on a 1 s grid, four by hand."""
    total = np.zeros(round(32 * RATE))
    times = []
    t = 1.0
    for _ in range(4):
        times.append((t, before))
        t += 1.1
    t += 3.0
    for _ in range(8):
        times.append((t, pattern))
        t += 1.0
    t += 3.0
    for _ in range(4):
        times.append((t, after))
        t += 0.9
    for at, hit in times:
        start = round(at * RATE)
        total[start : start + len(hit)] += hit
    total += np.random.default_rng(1).normal(0, 0.0005, len(total))
    sf.write(str(path), total, RATE, subtype="PCM_16")
    return [at for at, _ in times]


def test_groups_split_on_long_gaps():
    assert groups_of([1.0, 2.0, 3.0, 6.0, 7.0, 7.5, 11.0]) == [[0, 1, 2], [3, 4, 5], [6]]


def test_live_state_kept(tmp_path):
    path = tmp_path / "playback.wav"
    full, dull = saw(), low_passed(saw())
    recording(path, dull, full, dull)
    report = analyze(path, SETTINGS)
    assert report["group_sizes"] == [4, 8, 4]
    assert report["outcome"] == "audition_keeps_live_state"
    assert report["live_filter_before_pattern"] == "low_pass"
    assert report["live_filter_after_pattern"] == "low_pass"
    assert report["groups_by_name"]["pattern"]["type"] == "flat"


def test_locks_followed(tmp_path):
    path = tmp_path / "playback.wav"
    full, dull = saw(), low_passed(saw())
    recording(path, dull, full, full)
    report = analyze(path, SETTINGS)
    assert report["outcome"] == "audition_follows_last_lock"
    assert report["comparisons"] == {
        "before_matches_pattern": False,
        "after_matches_pattern": True,
        "before_matches_after": False,
    }


def test_indistinguishable(tmp_path):
    path = tmp_path / "playback.wav"
    full = saw()
    recording(path, full, full, full)
    assert analyze(path, SETTINGS)["outcome"] == "indistinguishable"


def test_missing_group_is_other(tmp_path):
    path = tmp_path / "playback.wav"
    total = np.zeros(round(10 * RATE))
    hit = saw()
    for at in (1.0, 2.0, 3.0, 4.0):
        total[round(at * RATE) : round(at * RATE) + len(hit)] += hit
    sf.write(str(path), total, RATE, subtype="PCM_16")
    report = analyze(path, SETTINGS)
    assert report["outcome"] == "other"
    assert "1 groups" in report["reason"]


def test_outcomes_listed():
    assert set(OUTCOMES) == {
        "audition_follows_last_lock",
        "audition_keeps_live_state",
        "indistinguishable",
        "other",
    }
    assert "indistinguishable" in OUTCOMES


@pytest.mark.parametrize("fraction", [0.05, 0.1])
def test_quiet_auditions_still_detected(tmp_path, fraction):
    path = tmp_path / "playback.wav"
    full = saw()
    recording(
        path, low_passed(full) * fraction / 0.5 * 2, full, low_passed(full) * fraction / 0.5 * 2
    )
    assert analyze(path, SETTINGS)["group_sizes"] == [4, 8, 4]
