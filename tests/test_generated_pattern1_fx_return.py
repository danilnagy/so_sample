"""Generated octave-down/clear keep the global fixed and require exact whole-body return."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_pattern1_fx_return import reception_checks, require_down_result
from scripts.prepare_generated_pattern1_fx_return import (
    LEGS,
    REGISTRATION,
    fixed_return_packets,
    return_checks,
)


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    if not registration_path.exists():
        pytest.skip("Generated fixed-return registration required")
    registration = json.loads(registration_path.read_text())
    up = decode_artifact(load_artifact(root / registration["source_artifact"]))
    baseline = decode_artifact(load_artifact(root / registration["independent_clear_artifact"]))
    targets = {
        leg: decode_artifact(
            load_artifact(root / "experiments" / spec["experiment_id"] / "edited.symbols.npz")
        )
        for leg, spec in LEGS.items()
    }
    return root, registration, up, targets, baseline


@pytest.mark.capture
@pytest.mark.parametrize("leg", ["down", "clear"])
def test_actual_generated_waveforms_native_exact_and_clear_entire_independent_baseline(states, leg):
    root, registration, up, targets, baseline = states
    spec = next(item for item in registration["expected_capture_sequence"] if item["leg"] == leg)
    folder = root / "experiments" / spec["experiment_id"]
    recovered = decode_artifact(load_artifact(folder / "redecoded.symbols.npz"))
    base = up if leg == "down" else targets["down"]
    assert all(reception_checks(base, targets[leg], recovered, leg, baseline).values())
    assert tuple(fixed_return_packets(base, leg)) == targets[leg].packets
    validation_path = folder / "software-validation.json"
    validation = json.loads(validation_path.read_text())
    assert validation["passed"] and all(validation["checks"].values())
    assert not validation["hardware_verified"]
    for path, key in (
        (folder / "restore.wav", "restore_wav_sha256"),
        (folder / "edited.symbols.npz", "edited_artifact_sha256"),
        (validation_path, "software_validation_sha256"),
    ):
        assert sha256_file(path) == spec[key]
    if leg == "clear":
        assert recovered.packets == baseline.packets
        assert recovered.encoded_body == baseline.encoded_body


@pytest.mark.capture
@pytest.mark.parametrize(
    "leg,packet_index,offset",
    [
        ("down", 2, 131),
        ("down", 2, 130),
        ("down", 4, 1),
        ("clear", 2, 131),
        ("clear", 240, 15),
        ("clear", 8, 4),
    ],
)
def test_valid_native_other_global_note_sample_and_wrong_footer_changes_fail_exact_targets(
    states, leg, packet_index, offset
):
    _, _, up, targets, baseline = states
    base = up if leg == "down" else targets["down"]
    packets = list(targets[leg].packets)
    payload = bytearray(packets[packet_index].payload)
    payload[offset] ^= 1
    packets[packet_index] = Packet(packets[packet_index].tag, bytes(payload))
    actual = decode_frame(bytes(4095) + encode_packets(packets))
    checks = reception_checks(base, targets[leg], actual, leg, baseline)
    assert checks["source_and_actual_native_valid"]
    assert not checks["entire_actual_body_and_packets_match_target"]
    assert not checks["entire_fixed_leg_target_body_exact"]
    if leg == "clear":
        assert not checks["entire_independent_clear_body_and_packets_return"]


@pytest.mark.capture
def test_earlier_genuine_down_with_global1_cannot_substitute_for_new_global7_target(states):
    root, _, up, targets, baseline = states
    path = (
        root
        / "experiments/event-066-b-pattern1-FX8-recorded/derived/analysis-001/capture.symbols.npz"
    )
    recorded = decode_artifact(load_artifact(path))
    checks = reception_checks(up, targets["down"], recorded, "down", baseline)
    assert checks["all16_footer_nibbles_match_fixed_leg"]
    assert not checks["global131_stays7"]
    assert not checks["only_eight_Pattern1_footer_bytes_changed"]
    assert not checks["entire_actual_body_and_packets_match_target"]


@pytest.mark.capture
@pytest.mark.parametrize("leg", ["down", "clear"])
def test_wrong_source_state_and_leg_cannot_construct_or_validate(states, leg):
    _, _, _, targets, baseline = states
    with pytest.raises(ValueError, match="Exact fixed-leg"):
        fixed_return_packets(baseline, leg)
    assert not return_checks(baseline, targets[leg], leg)["source_is_exact_fixed_leg_body"]
    with pytest.raises(ValueError, match="Only fixed"):
        fixed_return_packets(baseline, "up")


@pytest.mark.parametrize(
    "field", ["passed", "checks", "registration_sha256", "capture_sha256", "artifact_sha256"]
)
def test_clear_gate_requires_successful_down_and_matching_evidence(field):
    valid = {
        "passed": True,
        "checks": {"native_exact": True},
        "registration_sha256": "r",
        "capture_sha256": "c",
        "artifact_sha256": "a",
    }
    require_down_result(valid, "r", "c", "a")
    invalid = copy.deepcopy(valid)
    invalid[field] = (
        False if field == "passed" else {"native_exact": False} if field == "checks" else "stale"
    )
    with pytest.raises(ValueError, match="down reception must pass"):
        require_down_result(invalid, "r", "c", "a")
