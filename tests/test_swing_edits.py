"""Hardware-grounded swing plans, literal preservation and composition with tempo."""

import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.edits import apply_plan
from po33_re.formats.globals import (
    calibrated_swing,
    calibrated_tempo,
    set_calibrated_swing,
    set_calibrated_tempo,
    set_calibrated_tempo_preset,
)
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.symbols import load_artifact


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-swing-timing6-001"
    if not (folder / "hardware-observation-001.json").exists():
        pytest.skip("Accepted swing6 restore required")
    observation = json.loads((folder / "hardware-observation-001.json").read_text())
    assert observation["hardware_verified"] and observation["swing_writer_verified"]
    path = root / observation["artifact_path"]
    assert sha256_file(path) == observation["artifact_sha256"]
    current = decode_artifact(load_artifact(path))
    pair = json.loads((root / "experiments/swing-timing-pair-registration-001.json").read_text())
    base_path = root / pair["source_artifact"]
    maximum = decode_artifact(load_artifact(base_path))
    return root, path, current, base_path, maximum


@pytest.mark.capture
def test_public_swing_reconstructs_entire_independent_physical_range(states):
    root, _, current, _, maximum = states
    for value, name in (
        (0, "event-038-b-swing-minimum"),
        (9, "event-039-c-swing-9"),
        (18, "event-040-a-return-swing18"),
    ):
        genuine = decode_artifact(
            load_artifact(root / "experiments" / name / "derived/analysis-001/capture.symbols.npz")
        )
        assert calibrated_swing(genuine) == value
        assert encode_packets(set_calibrated_swing(maximum, value)) == genuine.encoded_body
    assert calibrated_swing(current) == 6 and set_calibrated_swing(current, 6) == current.packets


@pytest.mark.capture
def test_tempo_and_swing_commute_without_resetting_the_other_field(states):
    source = states[2]
    tempo_first = native(set_calibrated_swing(native(set_calibrated_tempo(source, 100)), 9))
    swing_first = native(set_calibrated_tempo(native(set_calibrated_swing(source, 9)), 100))
    assert tempo_first.packets == swing_first.packets
    assert (calibrated_tempo(tempo_first), calibrated_swing(tempo_first)) == (100, 9)
    assert source.packets[2].payload[129:131] == bytes([137, 6])
    assert (
        source.packets[:2] == tempo_first.packets[:2]
        and source.packets[3:] == tempo_first.packets[3:]
    )
    assert tempo_first.packets[2].payload[:129] == source.packets[2].payload[:129]
    assert tempo_first.packets[2].payload[131:] == source.packets[2].payload[131:]
    preset_source = native(set_calibrated_tempo(source, 120))
    assert native(set_calibrated_tempo_preset(preset_source, 80)).packets[2].payload[130] == 6


@pytest.mark.capture
@pytest.mark.parametrize("value", [True, False, -1, 19, 255, 6.0, "6", None])
def test_invalid_swing_target_rejected(states, value):
    with pytest.raises(ValueError, match="integer from 0 to 18"):
        set_calibrated_swing(states[2], value)


@pytest.mark.capture
@pytest.mark.parametrize("value", [19, 128, 255])
def test_unknown_source_swing_prevents_both_global_writers(states, value):
    packets = list(states[2].packets)
    data = bytearray(packets[2].payload)
    data[130] = value
    packets[2] = Packet(0x7D5C, bytes(data))
    for operation, target in ((set_calibrated_swing, 6), (set_calibrated_tempo, 100)):
        with pytest.raises(ValueError, match="Unknown opaque global context"):
            operation(native(packets), target)


@pytest.mark.capture
@pytest.mark.parametrize("index,offset", [(1, 0), (2, 128), (2, 131), (2, 254)])
def test_unrecognized_opaque_bytes_prevent_swing_edit(states, index, offset):
    packets = list(states[2].packets)
    data = bytearray(packets[index].payload)
    data[offset] ^= 1
    packets[index] = Packet(0x7D5C, bytes(data))
    with pytest.raises(ValueError, match="Unknown opaque global context"):
        set_calibrated_swing(native(packets), 0)


@pytest.mark.capture
def test_source_tempo_outside_bounds_prevents_swing_edit(states):
    packets = list(states[2].packets)
    data = bytearray(packets[2].payload)
    data[129] = 59
    packets[2] = Packet(0x7D5C, bytes(data))
    with pytest.raises(ValueError, match="Source tempo"):
        set_calibrated_swing(native(packets), 0)


@pytest.mark.capture
@pytest.mark.parametrize("swing", [0, 6])
def test_public_compiler_replays_accepted_timing_wav_byte_for_byte(states, swing, tmp_path):
    root, _, _, source_path, _ = states
    plan = root / f"experiments/replay-swing{swing}-plan-001/plan.json"
    output = tmp_path / "compiled"
    before = source_path.read_bytes()
    assert (
        main(["apply-edits", str(source_path), "--plan", str(plan), "--out-dir", str(output)]) == 0
    )
    assert (output / "restore.wav").read_bytes() == (
        root / f"experiments/edited-swing-timing{swing}-001/restore.wav"
    ).read_bytes()
    assert not json.loads((output / "compile-report.json").read_text())["hardware_verified"]
    assert source_path.read_bytes() == before


@pytest.mark.capture
def test_hash_bound_joint_plan_keeps_sequential_trace_and_source_immutable(states):
    root, source_path, source, _, _ = states
    original = load_artifact(source_path)
    before = original.to_bytes()
    plan = json.loads((root / "experiments/joint-tempo100-swing9-plan-001/plan.json").read_text())
    edited, trace = apply_plan(original, sha256_file(source_path), plan)
    target = decode_artifact(edited)
    assert target.packets[2].payload[129:131] == bytes([100, 9])
    assert trace[0]["after_body_sha256"] == trace[1]["before_body_sha256"]
    assert trace[-1]["after_body_sha256"] == hashlib.sha256(target.encoded_body).hexdigest()
    assert not edited.metadata["hardware_verified"] and original.to_bytes() == before
    assert source.packets[3:] == target.packets[3:]
    with pytest.raises(ValueError, match="source artifact hash"):
        apply_plan(original, "0" * 64, plan)


@pytest.mark.capture
def test_actual_joint_capture_matches_public_plan_and_inverse_recovers_genuine_swing6(states):
    root, _, current, _, _ = states
    folder = root / "experiments/edited-joint-tempo100-swing9-001"
    observation_path = folder / "hardware-observation-001.json"
    if not observation_path.exists():
        pytest.skip("Accepted joint tempo/swing restore required")
    observation = json.loads(observation_path.read_text())
    assert (
        observation["hardware_verified"] and observation["joint_tempo_swing_composition_verified"]
    )
    path = root / observation["artifact_path"]
    assert sha256_file(path) == observation["artifact_sha256"]
    genuine = decode_artifact(load_artifact(path))
    assert (calibrated_tempo(genuine), calibrated_swing(genuine)) == (100, 9)
    predicted = native(set_calibrated_swing(native(set_calibrated_tempo(current, 100)), 9))
    assert predicted.encoded_body == genuine.encoded_body
    inverse = native(set_calibrated_swing(native(set_calibrated_tempo(genuine, 137)), 6))
    assert inverse.encoded_body == current.encoded_body
