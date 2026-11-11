"""Verify fixed generated volume mask and independent gain-direction measurements."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from po33_re.artifacts import json_bytes, sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_sound3_volume18_restore import restore_checks
from scripts.prepare_generated_sound3_volume18_pair import candidate_packets
from scripts.sound3_volume_gain_analysis import compare_reports, measure_channel


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-generated-volume18-pair-registration-001.json"
    if not path.exists():
        pytest.skip("Independent uniform21 reference and generated18 pair required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


@pytest.mark.capture
def test_candidate_changes_only_six_bits_per_cell_and_encodings_predict_opposite_gain(states):
    _, source, registration = states
    target = decode_frame(bytes(4095) + encode_packets(candidate_packets(source)))
    leg = registration["expected_capture_sequence"][1]
    assert all(restore_checks(source, target, target, leg, registration).values())
    before, after = pattern_data(source, 1), pattern_data(target, 1)
    for step in range(16):
        p = 48 * step + 6
        assert before[p] & 0x3F == after[p] & 0x3F
        assert before[p + 1] & 0xF0 == after[p + 1] & 0xF0
        assert after[p + 2] == before[p + 2]
        assert (after[p] >> 6) | ((after[p + 1] & 15) << 2) == 18
        assert ((after[p] >> 6) << 4) | (after[p + 1] & 15) == 36
    assert leg["contiguous_raw_code"] < 21 < leg["alternative_order_raw_code"]


@pytest.mark.capture
def test_reference_and_candidate_redecode_entire_registered_target_without_hardware_claim(states):
    root, source, registration = states
    for leg in registration["expected_capture_sequence"]:
        folder = root / "experiments" / leg["experiment_id"]
        target, recovered = [
            decode_artifact(load_artifact(folder / name))
            for name in ("edited.symbols.npz", "redecoded.symbols.npz")
        ]
        assert all(restore_checks(source, target, recovered, leg, registration).values())
        report = json.loads((folder / "software-validation.json").read_text())
        assert report["passed"] and not report["hardware_verified"]


@pytest.mark.capture
def test_source_guard_and_hidden_auxiliary_change_prevent_false_recapture_success(states):
    root, source, registration = states
    other = decode_artifact(
        load_artifact(
            root
            / "experiments/event-049-b-return-sound3-volume-lock-maximum/derived/analysis-001/capture.symbols.npz"
        )
    )
    with pytest.raises(ValueError, match="Exact independently"):
        candidate_packets(other)
    target = decode_frame(bytes(4095) + encode_packets(candidate_packets(source)))
    packets = list(target.packets)
    data = bytearray(packets[7].payload)
    assert data[786 - 3 * 255] == 0xFF
    data[786 - 3 * 255] = 0xF6
    packets[7] = Packet(packets[7].tag, bytes(data))
    bad = decode_frame(bytes(4095) + encode_packets(packets))
    assert not all(
        restore_checks(
            source, target, bad, registration["expected_capture_sequence"][1], registration
        ).values()
    )


@pytest.fixture(scope="module")
def method():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-volume18-gain-method-registration-001.json"
    if not path.exists():
        pytest.skip("Frozen gain method required")
    return json.loads(path.read_text())


def synthetic_audio(rate, amplitude):
    # Independent known sine bursts at step2 and13; input gain is a test oracle.
    values = np.random.default_rng(521).normal(0, 0.00005, round(11.2 * rate))
    for cycle in range(4):
        for offset in (0.20625, 1.8):
            begin = round((0.4 + 2.4 * cycle + offset) * rate)
            t = np.arange(round(0.30 * rate)) / rate
            fade = np.minimum(np.minimum(t / 0.005, (t[-1] - t) / 0.005), 1)
            values[begin : begin + len(t)] += amplitude * fade * np.sin(2 * np.pi * 500.65 * t)
    return values


@pytest.mark.parametrize("rate", [44100, 48000])
def test_fixed_method_recovers_known_tone_amplitude_and_pitch(method, rate):
    channel = measure_channel(synthetic_audio(rate, 0.06), rate, method["parameters"])
    assert channel["passed"]
    for measurement in channel["measurements"]:
        assert measurement["median_amplitude"] == pytest.approx(0.06, rel=0.01)
        assert measurement["median_frequency_hz"] == pytest.approx(500.65, abs=0.02)
        assert measurement["loop_median_seconds"] == pytest.approx(2.4, abs=0.002)
        assert len(measurement["steady_tone_fits"]) >= 7
    json_bytes(channel)


def summary(method, amplitude):
    # Comparison tests use independent known measurement summaries, not fitted values.
    measurements = [
        {
            "threshold_peak_fraction": fraction,
            "median_amplitude": amplitude,
            "median_frequency_hz": 500.65,
            "loop_median_seconds": 2.4,
            "usable": True,
        }
        for fraction in method["parameters"]["threshold_peak_fractions"]
    ]
    return {
        "parameters": method["parameters"],
        "channels": {
            "left": {"measurements": measurements},
            "right": {"measurements": measurements},
        },
        "passed": True,
    }


def test_gain_directions_discriminate_without_assuming_a_linear_curve(method):
    reference = summary(method, 0.06)
    quiet = compare_reports(reference, summary(method, 0.05), method)
    loud = compare_reports(reference, summary(method, 0.09), method)
    assert (
        quiet["all_contiguous_order_gain_directions_supported"]
        and not quiet["all_alternative_order_gain_directions_supported"]
    )
    assert (
        loud["all_alternative_order_gain_directions_supported"]
        and not loud["all_contiguous_order_gain_directions_supported"]
    )
    same = compare_reports(reference, reference, method)
    assert (
        not same["all_contiguous_order_gain_directions_supported"]
        and not same["all_alternative_order_gain_directions_supported"]
    )
    assert not quiet["hardware_verified"] and not quiet["gain_curve_or_numeric_UI_scale_confirmed"]


def test_pitch_shift_tempo_change_or_failed_audio_cannot_be_called_a_gain_edit(method):
    reference = summary(method, 0.06)
    for change in ("pitch", "tempo", "failed"):
        candidate = copy.deepcopy(summary(method, 0.05))
        if change == "failed":
            candidate["passed"] = False
        else:
            for channel in candidate["channels"].values():
                for measurement in channel["measurements"]:
                    measurement[
                        "median_frequency_hz" if change == "pitch" else "loop_median_seconds"
                    ] = 550 if change == "pitch" else 2.5
        result = compare_reports(reference, candidate, method)
        assert not result["all_contiguous_order_gain_directions_supported"]


def test_missing_threshold_or_changed_method_is_rejected(method):
    reference = summary(method, 0.06)
    candidate = copy.deepcopy(summary(method, 0.05))
    candidate["channels"]["left"]["measurements"].pop()
    with pytest.raises(ValueError, match="All three"):
        compare_reports(reference, candidate, method)
    candidate = copy.deepcopy(summary(method, 0.05))
    candidate["parameters"]["center_frequency_hz"] = 501
    with pytest.raises(ValueError, match="frozen method"):
        compare_reports(reference, candidate, method)
