"""Complementary first-byte probes keep native state exact; audio must not skip first tone."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_pattern1_fx_nibble_pair import reception_checks, require_native_result
from scripts.pattern1_fx_nibble_audio import PARAMETERS, audio_report, channel_report, compare_audio
from scripts.prepare_generated_pattern1_fx_nibble_pair import (
    LEGS,
    REGISTRATION,
    fixed_probe_packets,
    probe_checks,
)


def signal(first_frequency=530, first_duration=0.32, first_amplitude=0.2, rate=44100):
    values = np.zeros(3 * rate)
    for onset, frequency, duration, amplitude in (
        (0.8, first_frequency, first_duration, first_amplitude),
        (1.6, 850, 0.32, 0.2),
    ):
        start, count = round(onset * rate), round(duration * rate)
        values[start : start + count] = amplitude * np.sin(
            2 * np.pi * frequency * np.arange(count) / rate
        )
    return values


@pytest.mark.parametrize("frequency", [530, 1060, 1190, 2380])
def test_first_tone_frequency_fit_matches_independent_sine_before_later_different_note(frequency):
    report = channel_report(signal(frequency), 44100, PARAMETERS)
    assert report["passed"]
    for row in report["measurements"]:
        assert abs(row["fit"]["frequency_hz"] / frequency - 1) < 0.0001
        assert 0.79 < row["first_onset_seconds"] < 0.82


@pytest.mark.parametrize("duration,amplitude", [(0.04, 0.2), (0.32, 0.005)])
def test_short_or_quiet_first_tone_cannot_be_replaced_by_later_good_note(duration, amplitude):
    report = channel_report(
        signal(first_duration=duration, first_amplitude=amplitude), 44100, PARAMETERS
    )
    assert not report["passed"]
    assert not all(row["usable"] for row in report["measurements"])


def make_audio_report(path, frequency):
    values = signal(frequency)
    sf.write(path, np.column_stack((values, values * 0.95)), 44100, subtype="PCM_16")
    return audio_report(path, PARAMETERS)


@pytest.mark.parametrize(
    "a_frequency,b_frequency,classification",
    [
        (1060, 530, "low_nibble_first"),
        (530, 1060, "high_nibble_first"),
        (530, 530, "inconclusive"),
        (800, 530, "inconclusive"),
    ],
)
def test_both_order_models_and_inconclusive_ratios_stay_distinct(
    tmp_path, a_frequency, b_frequency, classification
):
    a = make_audio_report(tmp_path / "a.wav", a_frequency)
    b = make_audio_report(tmp_path / "b.wav", b_frequency)
    result = compare_audio(a, b, PARAMETERS)
    assert result["comparison_usable"]
    assert result["classification"] == classification
    assert not result["hardware_verified"] and not result["general_per_step_FX_writer_enabled"]


@pytest.mark.parametrize("damage", ["quality", "threshold", "parameters", "nan", "fit_failure"])
def test_bad_evidence_and_changed_method_do_not_confirm_order(tmp_path, damage):
    a = make_audio_report(tmp_path / "a.wav", 1060)
    b = make_audio_report(tmp_path / "b.wav", 530)
    damaged = copy.deepcopy(a)
    if damage == "parameters":
        damaged["parameters"] = dict(PARAMETERS, frequency_search_hz=[400, 2000])
    elif damage == "quality":
        damaged["passed"] = False
    elif damage == "threshold":
        damaged["channels"]["left"]["measurements"][0]["threshold_peak_fraction"] = 0.1
    elif damage == "nan":
        damaged["channels"]["left"]["measurements"][0]["fit"]["frequency_hz"] = float("nan")
    else:
        damaged["channels"]["left"]["measurements"][0]["fit"]["fit_success"] = False
    if damage in ("threshold", "parameters"):
        with pytest.raises(ValueError, match="differs"):
            compare_audio(damaged, b, PARAMETERS)
    else:
        result = compare_audio(damaged, b, PARAMETERS)
        assert not result["comparison_usable"]
        assert result["classification"] == "inconclusive"


def test_silence_clipping_stereo_disagreement_and_retuned_method_fail(tmp_path):
    silent_path = tmp_path / "silent.wav"
    sf.write(silent_path, np.zeros((44100, 2)), 44100, subtype="PCM_16")
    assert not audio_report(silent_path, PARAMETERS)["passed"]
    values = signal(530)
    values[40000] = 1
    sf.write(tmp_path / "clipped.wav", np.column_stack((values, values)), 44100, subtype="PCM_16")
    assert not audio_report(tmp_path / "clipped.wav", PARAMETERS)["checks"]["no_full_scale_samples"]
    sf.write(
        tmp_path / "stereo.wav",
        np.column_stack((signal(530), signal(1060))),
        44100,
        subtype="PCM_16",
    )
    assert not audio_report(tmp_path / "stereo.wav", PARAMETERS)["passed"]
    with pytest.raises(ValueError, match="frozen parameters"):
        channel_report(signal(), 44100, dict(PARAMETERS, minimum_fit_explained_variance=0.1))


@pytest.fixture(scope="module")
def source():
    root = Path(__file__).resolve().parents[1]
    path = (
        root / "experiments/edited-pattern1-FX6-7-halves-global7-001/hardware-observation-001.json"
    )
    if not path.exists():
        pytest.skip("Accepted mixed source required")
    observation = json.loads(path.read_text())
    return decode_artifact(load_artifact(root / observation["artifact_path"]))


@pytest.mark.capture
def test_complementary_first_bytes_differ_only_in_that_byte_and_guard_unknown_source(source):
    frames = {
        leg: decode_frame(bytes(4095) + encode_packets(fixed_probe_packets(source, leg)))
        for leg in LEGS
    }
    for leg, frame in frames.items():
        assert all(probe_checks(source, frame, leg).values())
    a, b = [pattern_data(frames[leg], 1) for leg in LEGS]
    assert [i for i, (x, y) in enumerate(zip(a, b)) if x != y] == [1024]
    assert a[1024:] == bytes([0xF6]) + bytes([255]) * 7
    assert b[1024:] == bytes([0x6F]) + bytes([255]) * 7
    with pytest.raises(ValueError, match="Exact accepted mixed"):
        fixed_probe_packets(frames["a"], "a")


@pytest.mark.capture
@pytest.mark.parametrize("packet_index,offset", [(2, 131), (2, 130), (4, 6), (240, 15)])
def test_hidden_global_note_or_sample_changes_fail_native_preservation(
    source, packet_index, offset
):
    packets = list(fixed_probe_packets(source, "a"))
    payload = bytearray(packets[packet_index].payload)
    payload[offset] ^= 1
    packets[packet_index] = Packet(packets[packet_index].tag, bytes(payload))
    actual = decode_frame(bytes(4095) + encode_packets(packets))
    report = probe_checks(source, actual, "a")
    assert report["source_and_actual_native_valid"]
    assert not report["only_eight_Pattern1_footer_bytes_changed"]


@pytest.mark.capture
@pytest.mark.parametrize("leg", list(LEGS))
def test_actual_generated_first_pair_waveforms_and_frozen_method_pins(source, leg):
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments" / REGISTRATION
    if not path.exists():
        pytest.skip("Frozen first-pair registration required")
    registration = json.loads(path.read_text())
    spec = next(item for item in registration["expected_capture_sequence"] if item["leg"] == leg)
    folder = root / "experiments" / spec["experiment_id"]
    target, recovered = [
        decode_artifact(load_artifact(folder / name))
        for name in ("edited.symbols.npz", "redecoded.symbols.npz")
    ]
    assert all(reception_checks(source, target, recovered, spec).values())
    assert registration["audio_parameters"] == PARAMETERS
    assert (
        sha256_file(root / "scripts/pattern1_fx_nibble_audio.py")
        == registration["audio_method_script_sha256"]
    )
    assert (
        sha256_file(root / "scripts/sound3_pitch_frequency_analysis.py")
        == registration["frequency_fit_helper_sha256"]
    )
    assert sha256_file(folder / "restore.wav") == spec["restore_wav_sha256"]
    stale = dict(spec, expected_body_sha256="0" * 64)
    assert not reception_checks(source, target, recovered, stale)[
        "target_body_matches_registration"
    ]


@pytest.mark.parametrize(
    "field", ["passed", "checks", "registration_sha256", "capture_sha256", "artifact_sha256"]
)
def test_audio_requires_both_valid_native_results_with_matching_hashes(field):
    valid = {
        "passed": True,
        "checks": {"full_target": True},
        "registration_sha256": "r",
        "capture_sha256": "c",
        "artifact_sha256": "a",
    }
    require_native_result(valid, "r", "c", "a")
    damaged = dict(valid)
    damaged[field] = (
        False if field == "passed" else {"full_target": False} if field == "checks" else "stale"
    )
    with pytest.raises(ValueError, match="native targets must pass"):
        require_native_result(damaged, "r", "c", "a")
