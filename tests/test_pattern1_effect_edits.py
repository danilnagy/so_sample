"""Public uniform effects replay complete independent bodies without masking globals."""

import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import json_bytes, sha256_file
from po33_re.edits import apply_plan, compile_edit_plan
from po33_re.formats.effects import calibrated_pattern1_effect, set_calibrated_pattern1_effect
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact

FOLDERS = {
    "none": "edited-pattern1-FX15-global7-clear-001",
    "octave_up": "edited-pattern1-FX6-global7-up-001",
    "octave_down": "edited-pattern1-FX7-global7-down-001",
}


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    frames = {}
    for effect, folder in FOLDERS.items():
        path = root / "experiments" / folder / "hardware-observation-001.json"
        if not path.exists():
            pytest.skip("Independent generated effect hardware observations required")
        observation = json.loads(path.read_text())
        assert observation["hardware_verified"] and all(observation["checks"].values())
        artifact_path = root / observation["artifact_path"]
        assert sha256_file(artifact_path) == observation["artifact_sha256"]
        frames[effect] = decode_artifact(load_artifact(artifact_path))
    return root, frames


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.mark.capture
@pytest.mark.parametrize("before", list(FOLDERS))
@pytest.mark.parametrize("after", list(FOLDERS))
def test_all_supported_transitions_equal_independent_hardware_bodies_and_packets(
    states, before, after
):
    base = states[1][before]
    expected = states[1][after]
    original = base.encoded_body
    assert calibrated_pattern1_effect(base) == before
    actual = native(set_calibrated_pattern1_effect(base, after))
    assert actual.packets == expected.packets and actual.encoded_body == expected.encoded_body
    assert calibrated_pattern1_effect(actual) == after
    assert actual.packets[2].payload[131] == 7
    assert pattern_data(actual, 1)[:1024] == pattern_data(base, 1)[:1024]
    assert base.encoded_body == original
    if before == after:
        assert actual.encoded_body == original


@pytest.mark.capture
@pytest.mark.parametrize(
    "effect", [True, False, None, 6, 7, 15, 6.0, "reverse", "6", "OCTAVE_UP", [], {}]
)
def test_only_named_calibrated_effects_allowed(states, effect):
    with pytest.raises(ValueError, match="Effect must be"):
        set_calibrated_pattern1_effect(states[1]["none"], effect)


@pytest.mark.capture
@pytest.mark.parametrize(
    "packet_index,offset", [(2, 129), (2, 130), (2, 131), (4, 6), (7, 6), (13, 1), (240, 15)]
)
def test_unknown_global_note_parameter_key_other_pattern_and_sample_context_rejected(
    states, packet_index, offset
):
    packets = list(states[1]["none"].packets)
    payload = bytearray(packets[packet_index].payload)
    payload[offset] ^= 1
    packets[packet_index] = Packet(packets[packet_index].tag, bytes(payload))
    with pytest.raises(ValueError, match="Unknown Pattern1 effect context"):
        set_calibrated_pattern1_effect(native(packets), "octave_up")


@pytest.mark.capture
@pytest.mark.parametrize(
    "footer", [bytes([0xF7]) + bytes([0xFF]) * 7, bytes([0x77]) * 4 + bytes([0x66]) * 4, bytes(8)]
)
def test_mixed_and_unobserved_effect_sources_rejected(states, footer):
    base = states[1]["none"]
    data = bytearray(pattern_data(base, 1))
    data[1024:] = footer
    with pytest.raises(ValueError, match="Mixed Pattern1|Only uniform"):
        set_calibrated_pattern1_effect(native(_replace_pattern_data(base, 1, bytes(data))), "none")


def plan_for(path, effect):
    frame = decode_artifact(load_artifact(path))
    return {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(path),
        "source_body_sha256": hashlib.sha256(frame.encoded_body).hexdigest(),
        "operations": [{"operation": "set_pattern1_effect", "effect": effect}],
    }


@pytest.mark.capture
@pytest.mark.parametrize("effect", list(FOLDERS))
def test_public_compiler_replays_accepted_restore_wav_and_entire_native_body(
    states, tmp_path, effect
):
    root, frames = states
    source_path = (
        root
        / "experiments"
        / (
            "event-070-b-pattern1-plain-playback/derived/analysis-001/capture.symbols.npz"
            if effect == "octave_up"
            else "edited-pattern1-FX6-global7-up-001/derived/analysis-001/capture.symbols.npz"
            if effect == "octave_down"
            else "edited-pattern1-FX7-global7-down-001/edited.symbols.npz"
        )
    )
    before = source_path.read_bytes()
    plan_path = tmp_path / "plan.json"
    plan_path.write_bytes(json_bytes(plan_for(source_path, effect)))
    output = tmp_path / "compiled"
    report = compile_edit_plan(source_path, plan_path, output)
    assert report["passed"] and not report["hardware_verified"]
    recovered = decode_artifact(load_artifact(output / "redecoded.symbols.npz"))
    assert recovered.packets == frames[effect].packets
    assert recovered.encoded_body == frames[effect].encoded_body
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments" / FOLDERS[effect] / "restore.wav"
    ).read_bytes()
    assert source_path.read_bytes() == before


@pytest.mark.capture
def test_public_plan_hashes_and_extra_arguments_rejected(states):
    path = (
        states[0]
        / "experiments/edited-pattern1-FX15-global7-clear-001/derived/analysis-001/capture.symbols.npz"
    )
    source = load_artifact(path)
    plan = plan_for(path, "octave_down")
    with pytest.raises(ValueError, match="source artifact hash"):
        apply_plan(source, "0" * 64, plan)
    plan["source_body_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source native-body hash"):
        apply_plan(source, sha256_file(path), plan)
    plan = plan_for(path, "none")
    plan["operations"][0]["pattern"] = 2
    with pytest.raises(ValueError, match="Unexpected or missing"):
        apply_plan(source, sha256_file(path), plan)
