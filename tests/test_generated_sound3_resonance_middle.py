"""Interior resonance evidence requires exact native state and both frozen amplitude bounds."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_sound3_resonance_middle import (
    compare_middle_audio,
    middle_reception_checks,
)
from scripts.prepare_generated_sound3_resonance_middle import fixed_middle_packets
from tests.test_generated_sound3_resonance_pair import audio_summary


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-generated-filter16-B32-middle-registration-001.json"
    if not path.exists():
        pytest.skip("Registered B32 middle required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    source = decode_artifact(load_artifact(source_path))
    folder = root / "experiments" / registration["experiment_id"]
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    return root, source, target, registration


@pytest.mark.capture
def test_exact_B32_wave_recovery_preserves_every_non_B_bit_and_binds_observed_endpoints(states):
    root, source, target, registration = states
    folder = root / "experiments" / registration["experiment_id"]
    recovered = decode_artifact(load_artifact(folder / "redecoded.symbols.npz"))
    assert (
        encode_packets(fixed_middle_packets(source))
        == target.encoded_body
        == recovered.encoded_body
    )
    assert all(middle_reception_checks(source, target, recovered, registration).values())
    assert (
        registration["registered_before_middle_native_and_audio"]
        and registration["endpoint_audio_already_observed"]
    )
    for item in registration["endpoint_inputs"]:
        assert sha256_file(root / item["audio_results"]) == item["audio_results_sha256"]
        observation = json.loads((root / item["observation"]).read_text())
        assert observation["hardware_verified"] and all(observation["checks"].values())
    assert not json.loads((folder / "software-validation.json").read_text())["hardware_verified"]


@pytest.mark.capture
@pytest.mark.parametrize("value", [True, 0, 31, 63, 32.0, "32"])
def test_only_fixed_middle_value_allowed(states, value):
    with pytest.raises(ValueError, match="Only fixed research"):
        fixed_middle_packets(states[1], value)


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 8, 770, 3, 1024])
def test_hidden_state_changes_cannot_be_rescued_by_correct_B32_values(states, offset):
    _, source, target, registration = states
    data = bytearray(pattern_data(target, 1))
    data[offset] ^= 1
    actual = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(target, 1, bytes(data)))
    )
    checks = middle_reception_checks(source, target, actual, registration)
    assert checks["all16_B_values_are32"]
    assert not checks["entire_actual_body_and_every_packet_match_target"]


@pytest.mark.capture
def test_wrong_source_or_stale_prediction_rejected(states):
    _, source, target, registration = states
    with pytest.raises(ValueError, match="Exact accepted"):
        fixed_middle_packets(target)
    stale = copy.deepcopy(registration)
    stale["expected_body_sha256"] = "0" * 64
    assert not all(middle_reception_checks(source, target, target, stale).values())


@pytest.mark.parametrize(
    "middle_amplitude,expected", [(0.02, True), (0.01, False), (0.07, False), (0.08, False)]
)
def test_both_strict_amplitude_margins_required_without_rescuing_a_failed_prediction(
    states, middle_amplitude, expected
):
    registration = states[3]
    minimum = audio_summary(registration, 0.01)
    middle = audio_summary(registration, middle_amplitude)
    maximum = audio_summary(registration, 0.07)
    report = compare_middle_audio(minimum, middle, maximum, registration)
    assert report["both_comparisons_usable"]
    assert report["all_middle_amplitudes_between_endpoints_with_registered_margin"] is expected
    assert not report["general_resonance_law_or_bit7_role_confirmed"]


@pytest.mark.parametrize("damage", ["failed", "one_channel", "frequency", "loop", "missing"])
def test_inconsistent_or_unusable_middle_cannot_pass(states, damage):
    registration = states[3]
    minimum, middle, maximum = [audio_summary(registration, value) for value in (0.01, 0.02, 0.07)]
    if damage == "failed":
        middle["passed"] = False
    elif damage == "missing":
        middle["channels"]["right"]["measurements"].pop()
    else:
        for row in middle["channels"]["right"]["measurements"]:
            if damage == "one_channel":
                row["fits"] = [{"fundamental_amplitude": 0.01}]
            elif damage == "frequency":
                row["median_frequency_hz"] = 550
            else:
                row["loop_median_seconds"] = 2.41
    assert not compare_middle_audio(minimum, middle, maximum, registration)[
        "all_middle_amplitudes_between_endpoints_with_registered_margin"
    ]
