"""Exact pitch-mask construction and unbiased frequency estimation before pair audio."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.prepare_generated_sound3_pitch_pair import fixed_packets, pair_preservation
from scripts.sound3_pitch_frequency_analysis import (
    compare_frequency_reports,
    fit_frequency,
    measure_channel,
)


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-generated-pitch13-14-registration-001.json"
    if not path.exists():
        pytest.skip("Registered pitch pair required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


@pytest.mark.capture
def test_both_fixed_pitch_wavs_recover_exact_targets_and_preserve_volume_and_keys(states):
    root, source, registration = states
    for leg in registration["expected_capture_sequence"]:
        folder = root / "experiments" / leg["experiment_id"]
        target, recovered = [
            decode_artifact(load_artifact(folder / name))
            for name in ("edited.symbols.npz", "redecoded.symbols.npz")
        ]
        assert (
            encode_packets(fixed_packets(source, leg["raw_pitch_value"]))
            == target.encoded_body
            == recovered.encoded_body
        )
        assert all(pair_preservation(source, recovered, leg["raw_pitch_value"]).values())
        assert recovered.packets == target.packets
        assert not json.loads((folder / "software-validation.json").read_text())[
            "hardware_verified"
        ]


@pytest.mark.capture
def test_exact_source_fixed_values_and_auxiliary_guards_prevent_false_success(states):
    _, source, _ = states
    for value in (True, 1, 25, 13.0, "14"):
        with pytest.raises(ValueError, match="Only fixed research"):
            fixed_packets(source, value)
    target = decode_frame(bytes(4095) + encode_packets(fixed_packets(source, 13)))
    with pytest.raises(ValueError, match="Exact genuine"):
        fixed_packets(target, 14)
    data = bytearray(pattern_data(target, 1))
    data[770] ^= 1
    bad = decode_frame(bytes(4095) + encode_packets(_replace_pattern_data(target, 1, bytes(data))))
    assert not all(pair_preservation(source, bad, 13).values())


@pytest.fixture(scope="module")
def parameters(states):
    return states[2]["frequency_method"]["parameters"]


def synthetic_audio(rate, frequency):
    y = np.random.default_rng(912).normal(0, 0.00003, round(11.2 * rate))
    for cycle in range(4):
        for offset in (0.20625, 1.8):
            begin = round((0.4 + 2.4 * cycle + offset) * rate)
            t = np.arange(round(0.3 * rate)) / rate
            fade = np.minimum(np.minimum(t / 0.005, (t[-1] - t) / 0.005), 1)
            y[begin : begin + len(t)] += 0.04 * fade * np.sin(2 * np.pi * frequency * t)
    return y


@pytest.mark.parametrize("rate", [44100, 48000])
@pytest.mark.parametrize("frequency", [500.65, 530.42, 557.0])
def test_common_method_recovers_independent_frequencies_without_candidate_center_bias(
    parameters, rate, frequency
):
    channel = measure_channel(synthetic_audio(rate, frequency), rate, parameters)
    assert channel["passed"]
    for measurement in channel["measurements"]:
        assert measurement["median_frequency_hz"] == pytest.approx(frequency, abs=0.03)
        assert measurement["loop_median_seconds"] == pytest.approx(2.4, abs=0.002)
        assert measurement["usable"]


def summary(parameters, frequency):
    measurements = [
        {
            "threshold_peak_fraction": fraction,
            "median_frequency_hz": frequency,
            "loop_median_seconds": 2.4,
            "usable": True,
        }
        for fraction in parameters["threshold_peak_fractions"]
    ]
    return {
        "parameters": parameters,
        "channels": {
            name: {"measurements": copy.deepcopy(measurements)} for name in ("left", "right")
        },
        "passed": True,
    }


def test_interval_hypothesis_is_distinct_from_a_general_upward_shift(parameters):
    reference = summary(parameters, 500.65)
    semitone = compare_frequency_reports(
        reference, summary(parameters, 500.65 * 2 ** (1 / 12)), parameters
    )
    other = compare_frequency_reports(reference, summary(parameters, 500.65 * 1.1), parameters)
    same = compare_frequency_reports(reference, reference, parameters)
    assert (
        semitone["all_frequency_increases_supported"]
        and semitone["all_one_semitone_ratios_supported"]
    )
    assert (
        other["all_frequency_increases_supported"]
        and not other["all_one_semitone_ratios_supported"]
    )
    assert (
        not same["all_frequency_increases_supported"]
        and not same["all_one_semitone_ratios_supported"]
    )
    assert not semitone["hardware_verified"] and not semitone["pitch_field_writer_enabled"]


@pytest.mark.parametrize("damage", ["loop", "failed", "wrong_reference", "opposite_channel"])
def test_wrong_loop_failed_audio_reference_or_conflicting_channel_cannot_confirm_interval(
    parameters, damage
):
    reference = summary(parameters, 500.65)
    candidate = summary(parameters, 500.65 * 2 ** (1 / 12))
    if damage == "failed":
        candidate["passed"] = False
    elif damage == "wrong_reference":
        reference = summary(parameters, 550.0)
        candidate = summary(parameters, 550.0 * 2 ** (1 / 12))
    else:
        for item in candidate["channels"]["right"]["measurements"]:
            item["loop_median_seconds" if damage == "loop" else "median_frequency_hz"] = (
                2.5 if damage == "loop" else 480.0
            )
    report = compare_frequency_reports(reference, candidate, parameters)
    assert not report["all_one_semitone_ratios_supported"]


def test_changed_method_or_missing_threshold_is_rejected(parameters):
    reference = summary(parameters, 500.65)
    candidate = copy.deepcopy(summary(parameters, 530.42))
    candidate["parameters"]["frequency_search_hz"] = [490, 550]
    with pytest.raises(ValueError, match="frozen registration"):
        compare_frequency_reports(reference, candidate, parameters)
    candidate = summary(parameters, 530.42)
    candidate["channels"]["left"]["measurements"].pop()
    with pytest.raises(ValueError, match="Three usable"):
        compare_frequency_reports(reference, candidate, parameters)


def test_noise_does_not_become_a_good_sine_fit(parameters):
    values = np.random.default_rng(442).normal(0, 0.04, 4410)
    assert not fit_frequency(values, 44100, parameters)["fit_success"]
