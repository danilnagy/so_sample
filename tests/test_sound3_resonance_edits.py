"""Observed-code resonance plans reconstruct accepted bodies and preserve unrelated data."""

import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import json_bytes, sha256_file
from po33_re.edits import apply_plan, compile_edit_plan
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.formats.resonance import calibrated_sound3_resonances, set_calibrated_sound3_resonance
from po33_re.modem.symbols import load_artifact


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    folders = {
        0: "edited-sound3-filter16-B0-reference-001",
        32: "edited-sound3-filter16-B32-middle-001",
        63: "edited-sound3-filter16-B63-candidate-001",
    }
    frames = {}
    for value, name in folders.items():
        path = root / "experiments" / name / "hardware-observation-001.json"
        if not path.exists():
            pytest.skip("Accepted resonance controls required")
        observation = json.loads(path.read_text())
        assert observation["hardware_verified"] and all(observation["checks"].values())
        artifact_path = root / observation["artifact_path"]
        assert sha256_file(artifact_path) == observation["artifact_sha256"]
        frames[value] = decode_artifact(load_artifact(artifact_path))
    return root, frames, folders


@pytest.mark.capture
@pytest.mark.parametrize("source_value", [0, 32, 63])
def test_each_tested_source_reconstructs_all_three_independent_accepted_bodies(
    states, source_value
):
    frames = states[1]
    for value, independent in frames.items():
        assert calibrated_sound3_resonances(independent) == (value,) * 16
        assert (
            encode_packets(set_calibrated_sound3_resonance(frames[source_value], value))
            == independent.encoded_body
        )
    assert (
        set_calibrated_sound3_resonance(frames[source_value], source_value)
        == frames[source_value].packets
    )


@pytest.mark.capture
def test_legacy_note32_parameter0_source_and_neighbor_preservation(states):
    root, frames, _ = states
    legacy = decode_artifact(
        load_artifact(
            root
            / "experiments/edited-sound3-filter16-lowpass-001/derived/analysis-001/capture.symbols.npz"
        )
    )
    assert calibrated_sound3_resonances(legacy).count(32) == 5
    assert calibrated_sound3_resonances(legacy).count(0) == 11
    for value, accepted in frames.items():
        assert (
            encode_packets(set_calibrated_sound3_resonance(legacy, value)) == accepted.encoded_body
        )
    data = bytearray(pattern_data(frames[32], 1))
    data[3] ^= 1
    neighbor = native(_replace_pattern_data(frames[32], 1, bytes(data)))
    target = native(set_calibrated_sound3_resonance(neighbor, 63))
    assert pattern_data(target, 1)[3:6] == bytes(data[3:6])


@pytest.mark.capture
@pytest.mark.parametrize("value", [True, False, -1, 1, 16, 31, 33, 62, 64, 32.0, "63", None])
def test_only_observed_target_codes_and_integer_types_allowed(states, value):
    with pytest.raises(ValueError, match="integer in"):
        set_calibrated_sound3_resonance(states[1][32], value)


@pytest.mark.capture
@pytest.mark.parametrize(
    "damage", ["bit5", "pitch", "volume", "cutoff", "key", "new_note", "source31", "automation"]
)
def test_unknown_context_codes_and_automation_rejected(states, damage):
    base = states[1][32]
    data = bytearray(pattern_data(base, 1))
    if damage == "source31":
        data[8] = (data[8] & 3) | (31 << 2)
    elif damage == "automation":
        data[104] &= 3
    else:
        offset, mask = {
            "bit5": (6, 32),
            "pitch": (6, 1),
            "volume": (7, 1),
            "cutoff": (8, 1),
            "key": (770, 1),
            "new_note": (802, 1),
        }[damage]
        data[offset] ^= mask
    with pytest.raises(ValueError, match="Unknown Sound3 resonance"):
        set_calibrated_sound3_resonance(native(_replace_pattern_data(base, 1, bytes(data))), 0)


@pytest.mark.capture
def test_unknown_sample_window_rejected(states):
    base = states[1][32]
    packets = list(base.packets)
    index = sound_groups(base)[2][0]
    data = bytearray(packets[index].payload)
    data[4:8] = (19000).to_bytes(4, "little")
    packets[index] = Packet(packets[index].tag, bytes(data))
    with pytest.raises(ValueError, match="tested Sound3 window"):
        set_calibrated_sound3_resonance(native(packets), 0)


def plan_for(path, value):
    frame = decode_artifact(load_artifact(path))
    return {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(path),
        "source_body_sha256": hashlib.sha256(frame.encoded_body).hexdigest(),
        "operations": [{"operation": "set_sound3_resonance", "value": value}],
    }


@pytest.mark.capture
@pytest.mark.parametrize("value", [0, 32, 63])
def test_public_compiler_recovers_each_accepted_body_and_replays_endpoint_wavs(
    states, tmp_path, value
):
    root, frames, folders = states
    path = root / "experiments/edited-sound3-filter16-B0-reference-001/edited.symbols.npz"
    before = path.read_bytes()
    plan_path = tmp_path / "plan.json"
    plan_path.write_bytes(json_bytes(plan_for(path, value)))
    output = tmp_path / "compiled"
    report = compile_edit_plan(path, plan_path, output)
    assert report["passed"] and not report["hardware_verified"]
    recovered = decode_artifact(load_artifact(output / "redecoded.symbols.npz"))
    assert recovered.encoded_body == frames[value].encoded_body
    assert recovered.packets == frames[value].packets
    if value in (0, 63):
        assert (output / "restore.wav").read_bytes() == (
            root / "experiments" / folders[value] / "restore.wav"
        ).read_bytes()
    assert path.read_bytes() == before


@pytest.mark.capture
def test_stale_hashes_and_extra_arguments_rejected(states):
    root = states[0]
    path = root / "experiments/edited-sound3-filter16-B0-reference-001/edited.symbols.npz"
    source = load_artifact(path)
    before = source.to_bytes()
    plan = plan_for(path, 63)
    with pytest.raises(ValueError, match="source artifact hash"):
        apply_plan(source, "0" * 64, plan)
    plan["source_body_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source native-body hash"):
        apply_plan(source, sha256_file(path), plan)
    plan = plan_for(path, 63)
    plan["operations"][0]["step"] = 2
    with pytest.raises(ValueError, match="Unexpected or missing"):
        apply_plan(source, sha256_file(path), plan)
    assert source.to_bytes() == before
