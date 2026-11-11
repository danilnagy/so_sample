import numpy as np
import soundfile as sf

from scripts.pattern1_fx_step_pitch_method import classify_step1, decide, leg_step1, pitch_track

RATE = 44100
REFERENCE = 1190.417


def loop_signal(rise_in_step1, rise_in_step2=0.0):
    """One 2.4 s loop: a 210 ms tone whose pitch may rise in step 1 or step 2."""
    t = np.arange(round(0.21 * RATE)) / RATE
    ratio = np.ones_like(t)
    step1, step2 = t < 0.15, t >= 0.15
    ratio[step1] += rise_in_step1 * t[step1] / 0.15
    ratio[step2] = ratio[step1][-1] if rise_in_step1 else 1.0
    ratio[step2] += rise_in_step2 * (t[step2] - 0.15) / 0.06
    phase = 2 * np.pi * np.cumsum(REFERENCE * ratio) / RATE
    tone = 0.3 * np.sin(phase)
    return np.r_[tone, np.zeros(round(2.4 * RATE) - len(tone))]


def write_playback(path, rise_in_step1, rise_in_step2=0.0):
    loop = loop_signal(rise_in_step1, rise_in_step2)
    mono = np.r_[np.zeros(RATE), np.tile(loop, 6)]
    sf.write(path, np.column_stack((mono, mono)), RATE, subtype="PCM_16")


def test_flat_step1_is_none_and_rising_step1_is_effect(tmp_path):
    write_playback(tmp_path / "flat.wav", 0.0, rise_in_step2=0.15)
    write_playback(tmp_path / "rise.wav", 0.45)
    flat = leg_step1(pitch_track(tmp_path / "flat.wav"), REFERENCE)
    rise = leg_step1(pitch_track(tmp_path / "rise.wav"), REFERENCE)
    assert flat["median"]["class"] == "none"
    assert [loop["class"] for loop in flat["loops"]] == ["none"] * 5
    assert rise["median"]["class"] == "effect" and rise["median"]["max_ratio"] > 1.3
    assert decide(flat, rise)["classification"] == "high_nibble_first"
    assert decide(rise, flat)["classification"] == "low_nibble_first"


def test_small_drift_is_indeterminate_and_blocks_a_decision(tmp_path):
    write_playback(tmp_path / "drift.wav", 0.04)
    write_playback(tmp_path / "rise.wav", 0.45)
    drift = leg_step1(pitch_track(tmp_path / "drift.wav"), REFERENCE)
    rise = leg_step1(pitch_track(tmp_path / "rise.wav"), REFERENCE)
    assert drift["median"]["class"] == "indeterminate"
    assert decide(drift, rise)["classification"] == "inconclusive"


def test_too_few_loops_agreeing_is_inconclusive():
    none = {"class": "none"}
    effect = {"class": "effect"}
    a = {"median": none, "loops": [none, none, none, effect, effect]}
    b = {"median": effect, "loops": [effect] * 5}
    assert decide(a, b)["classification"] == "inconclusive"
    a["loops"] = [none, none, none, none, effect]
    assert decide(a, b)["classification"] == "high_nibble_first"


def test_quiet_windows_are_ignored():
    times = [float(t) for t in range(0, 200, 10)]
    hz = [REFERENCE] * len(times)
    quiet = [0.05] * len(times)
    assert classify_step1(times, hz, quiet, REFERENCE)["class"] == "indeterminate"


def test_digital_silence_gives_finite_values(tmp_path):
    import json

    write_playback(tmp_path / "rise.wav", 0.45)
    track = pitch_track(tmp_path / "rise.wav")
    json.dumps(track, allow_nan=False)
