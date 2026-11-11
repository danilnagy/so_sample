"""Check measured timing against independent synthetic delays and retained straight audio."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from po33_re.artifacts import json_bytes
from scripts.check_swing_timing_pair_audio import compare_reports
from scripts.swing_timing_analysis import audio_report, measure_onsets


@pytest.fixture(scope="module")
def registration():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/swing-timing-measurement-registration-001.json"
    if not path.exists():
        pytest.skip("Straight-calibrated measurement registration required")
    return json.loads(path.read_text())


def synthetic(rate, delay=0.0, bpm=137):
    loop = 16 * 60 / (bpm * 4)
    values = np.random.default_rng(405).normal(0, 0.0001, round((6 * loop + 1) * rate))
    for cycle in range(6):
        for offset in (loop / 16 + delay, 12 * loop / 16):
            begin = round((0.4 + cycle * loop + offset) * rate)
            t = np.arange(round(0.18 * rate)) / rate
            fade = np.minimum(np.minimum(t / 0.005, (t[-1] - t) / 0.005), 1)
            values[begin : begin + len(t)] += 0.06 * fade * np.sin(2 * np.pi * 500.65 * t)
    return values


def report(values, rate, reg):
    channel = measure_onsets(values, rate, reg["parameters"])
    passed = all(
        channel[key]
        for key in (
            "thresholds_agree",
            "all_alternating_gaps_consistent",
            "all_loops_near_registered137_bpm",
        )
    )
    return {
        "parameters": reg["parameters"],
        "channels": {"left": channel, "right": channel},
        "passed": passed,
    }


@pytest.mark.parametrize("rate", [44100, 48000])
def test_recovers_independent_positive_offbeat_delay_without_tempo_change(registration, rate):
    straight = report(synthetic(rate), rate, registration)
    swung = report(synthetic(rate, delay=0.035), rate, registration)
    result = compare_reports(straight, swung, registration)
    assert result["timing_hypotheses_supported"]
    for item in result["measurements"]:
        assert item["short_gap_delta_seconds"] == pytest.approx(0.035, abs=0.002)
        assert item["long_gap_delta_seconds"] == pytest.approx(-0.035, abs=0.002)
        assert item["loop_delta_seconds"] == pytest.approx(0, abs=0.001)
    assert not result["hardware_verified"] and not result["numeric_timing_units_confirmed"]
    json_bytes(result)


def test_same_timing_cannot_confirm_swing_effect(registration):
    straight = report(synthetic(44100), 44100, registration)
    assert not compare_reports(straight, straight, registration)["timing_hypotheses_supported"]


def test_changed_tempo_is_not_misreported_as_swing(registration):
    straight = report(synthetic(44100), 44100, registration)
    faster = report(synthetic(44100, bpm=145), 44100, registration)
    result = compare_reports(straight, faster, registration)
    assert not result["timing_hypotheses_supported"]
    assert any(not item["checks"]["whole_loop_period_preserved"] for item in result["measurements"])


def test_noise_or_insufficient_cycles_do_not_produce_timing_evidence(registration):
    with pytest.raises(ValueError, match="absent or below"):
        measure_onsets(np.zeros(44100 * 8), 44100, registration["parameters"])
    with pytest.raises(ValueError, match="seven resolvable"):
        measure_onsets(synthetic(44100)[: 3 * 44100], 44100, registration["parameters"])
    with pytest.raises(ValueError, match="finite"):
        measure_onsets(np.full(44100, np.nan), 44100, registration["parameters"])


def test_target_cannot_change_registered_frequency_or_drop_failed_threshold(registration):
    straight = report(synthetic(44100), 44100, registration)
    changed = copy.deepcopy(straight)
    changed["parameters"]["center_frequency_hz"] = 501
    with pytest.raises(ValueError, match="frozen"):
        compare_reports(straight, changed, registration)
    missing = copy.deepcopy(straight)
    missing["channels"]["left"]["measurements"].pop()
    with pytest.raises(ValueError, match="All three"):
        compare_reports(straight, missing, registration)


@pytest.mark.capture
def test_genuine_straight_playback_has_stereo_agreement_and_expected5_and11_step_gaps(registration):
    path = Path(__file__).resolve().parents[1] / "experiments/edited-swing-timing0-001/playback.wav"
    if not path.exists():
        pytest.skip("Straight-control ordinary audio required")
    result = audio_report(path, registration)
    assert result["passed"] and result["source_sha256"] == registration["straight_playback_sha256"]
    for channel in result["channels"].values():
        for measurement in channel["measurements"]:
            loop = measurement["loop_median_seconds"]
            assert measurement["complete_nonoverlapping_cycles"] >= 3
            assert measurement["short_gap_median_seconds"] == pytest.approx(
                loop * 5 / 16, abs=0.005
            )
            assert measurement["long_gap_median_seconds"] == pytest.approx(
                loop * 11 / 16, abs=0.005
            )
    json_bytes(result)
