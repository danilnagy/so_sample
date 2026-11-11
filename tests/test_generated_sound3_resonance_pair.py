"""Fixed resonance pair preserves non-FILTER state and requires frozen usable audio."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_sound3_resonance_restore import reception_checks
from scripts.prepare_generated_sound3_resonance_pair import fixed_packets
from scripts.sound3_resonance_audio import compare_resonance_audio, reference_audio_supported


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-generated-filter16-B0-B63-registration-001.json"
    if not path.exists():
        pytest.skip("Registered resonance pair required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


@pytest.mark.capture
@pytest.mark.parametrize("index", [0, 1])
def test_frozen_pair_has_complete_exact_waveform_recovery_without_hardware_claim(states, index):
    root, source, registration = states
    leg = registration["expected_capture_sequence"][index]
    folder = root / "experiments" / leg["experiment_id"]
    target, recovered = [
        decode_artifact(load_artifact(folder / name))
        for name in ("edited.symbols.npz", "redecoded.symbols.npz")
    ]
    assert (
        encode_packets(fixed_packets(source, leg["raw_B_value"]))
        == target.encoded_body
        == recovered.encoded_body
    )
    assert target.packets == recovered.packets
    assert all(reception_checks(source, target, recovered, leg, registration).values())
    for name, key in (
        ("restore.wav", "restore_wav_sha256"),
        ("edited.symbols.npz", "edited_artifact_sha256"),
        ("software-validation.json", "software_validation_sha256"),
    ):
        assert sha256_file(folder / name) == leg[key]
    assert not json.loads((folder / "software-validation.json").read_text())["hardware_verified"]


@pytest.mark.capture
def test_pair_differs_only_in_six_B_bits_and_method_is_original_common_method(states):
    root, _, registration = states
    frames = [
        decode_artifact(
            load_artifact(root / "experiments" / leg["experiment_id"] / "edited.symbols.npz")
        )
        for leg in registration["expected_capture_sequence"]
    ]
    a, b = [bytearray(pattern_data(frame, 1)) for frame in frames]
    for data in (a, b):
        for step in range(16):
            data[48 * step + 8] &= 3
    assert a == b
    original_path = root / registration["original_frequency_registration"]
    assert sha256_file(original_path) == registration["original_frequency_registration_sha256"]
    assert (
        registration["frequency_method"]
        == json.loads(original_path.read_text())["frequency_method"]
    )
    assert registration["registered_before_both_native_captures_and_playback"]


@pytest.mark.capture
@pytest.mark.parametrize("value", [True, False, 1, 32, -1, 64, 63.0, "0"])
def test_fixed_source_and_only_two_B_codes_are_required(states, value):
    with pytest.raises(ValueError, match="Only fixed research"):
        fixed_packets(states[1], value)


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 8, 770, 3, 1024])
def test_hidden_edits_cannot_pass_complete_reception(states, offset):
    root, source, registration = states
    leg = registration["expected_capture_sequence"][0]
    target = decode_artifact(
        load_artifact(root / "experiments" / leg["experiment_id"] / "edited.symbols.npz")
    )
    data = bytearray(pattern_data(target, 1))
    data[offset] ^= 2 if offset == 8 else 1
    actual = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(target, 1, bytes(data)))
    )
    checks = reception_checks(source, target, actual, leg, registration)
    assert not checks["entire_actual_body_and_packets_equal_target"]
    with pytest.raises(ValueError, match="Exact genuine"):
        fixed_packets(actual, 63)


def audio_summary(registration, amplitude=0.04):
    measurements = [
        {
            "threshold_peak_fraction": fraction,
            "median_frequency_hz": 530.26,
            "loop_median_seconds": 2.4,
            "usable": True,
            "fits": [{"fundamental_amplitude": amplitude}] * 7,
        }
        for fraction in registration["frequency_method"]["parameters"]["threshold_peak_fractions"]
    ]
    return {
        "parameters": copy.deepcopy(registration["frequency_method"]["parameters"]),
        "passed": True,
        "channels": {
            channel: {"measurements": copy.deepcopy(measurements)} for channel in ("left", "right")
        },
    }


def test_increase_is_a_separate_hypothesis_and_valid_unchanged_or_decreasing_audio_is_retained(
    states,
):
    registration = states[2]
    reference = audio_summary(registration)
    assert reference_audio_supported(reference, registration)
    for amplitude, expected in ((0.044, True), (0.04, False), (0.03, False)):
        report = compare_resonance_audio(
            reference, audio_summary(registration, amplitude), registration
        )
        assert report["comparison_usable"]
        assert report["all_amplitude_increases_supported"] is expected
        assert not report["general_resonance_law_or_broad_spectral_response_confirmed"]
        assert not report["resonance_writer_enabled"]


@pytest.mark.parametrize(
    "damage", ["failed", "one_channel", "frequency", "loop", "no_fits", "no_loop"]
)
def test_failed_or_inconsistent_candidate_measurements_cannot_pass(states, damage):
    registration = states[2]
    reference, candidate = audio_summary(registration), audio_summary(registration, 0.044)
    if damage == "failed":
        candidate["passed"] = False
    else:
        for row in candidate["channels"]["right"]["measurements"]:
            if damage == "one_channel":
                row["fits"] = [{"fundamental_amplitude": 0.04}]
            elif damage == "frequency":
                row["median_frequency_hz"] = 550
            elif damage == "loop":
                row["loop_median_seconds"] = 2.41
            elif damage == "no_fits":
                row["fits"] = []
            else:
                row["loop_median_seconds"] = None
    report = compare_resonance_audio(reference, candidate, registration)
    assert not report["all_amplitude_increases_supported"]


def test_missing_threshold_and_changed_method_fail_without_refitting(states):
    registration = states[2]
    reference, candidate = audio_summary(registration), audio_summary(registration, 0.044)
    candidate["channels"]["right"]["measurements"].pop()
    assert not compare_resonance_audio(reference, candidate, registration)["comparison_usable"]
    candidate = audio_summary(registration)
    candidate["parameters"]["center_frequency_hz"] = 531
    with pytest.raises(ValueError, match="frozen registration"):
        compare_resonance_audio(reference, candidate, registration)
    candidate = audio_summary(registration)
    candidate["channels"]["right"]["measurements"][1]["threshold_peak_fraction"] = 0.3
    with pytest.raises(ValueError, match="threshold sequence"):
        compare_resonance_audio(reference, candidate, registration)


def test_reference_must_be_usable_and_near_registered_pitch14_lead(states):
    registration = states[2]
    reference = audio_summary(registration)
    reference["channels"]["left"]["measurements"][0]["median_frequency_hz"] = 500
    assert not reference_audio_supported(reference, registration)
    assert not compare_resonance_audio(reference, audio_summary(registration, 0.044), registration)[
        "comparison_usable"
    ]
