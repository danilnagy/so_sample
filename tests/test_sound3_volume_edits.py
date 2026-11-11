"""Public bounded uniform volume must reproduce independent physical native bodies."""

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
from po33_re.formats.volume import calibrated_sound3_volumes, set_calibrated_sound3_volume
from po33_re.modem.symbols import load_artifact


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-sound3-volume36-002"
    observation_path = folder / "hardware-observation-001.json"
    if not observation_path.exists():
        pytest.skip("Physical reciprocal36 evidence required")
    observation = json.loads(observation_path.read_text())
    assert observation["hardware_verified"] and all(observation["checks"].values())
    path = root / observation["artifact_path"]
    assert sha256_file(path) == observation["artifact_sha256"]
    return root, path, decode_artifact(load_artifact(path))


@pytest.mark.capture
def test_uniform_writer_reconstructs_complete_independent_endpoint_and_interior_bodies(states):
    root, _, source = states
    for value, name in (
        (0, "event-045-c-sound3-tone-volume-lock-minimum"),
        (21, "event-047-d-sound3-volume-lock-quarter"),
        (63, "event-049-b-return-sound3-volume-lock-maximum"),
        (18, "edited-sound3-volume18-001"),
        (36, "edited-sound3-volume36-002"),
    ):
        genuine = decode_artifact(
            load_artifact(root / "experiments" / name / "derived/analysis-001/capture.symbols.npz")
        )
        assert calibrated_sound3_volumes(genuine) == (value,) * 16
        assert encode_packets(set_calibrated_sound3_volume(source, value)) == genuine.encoded_body
    assert set_calibrated_sound3_volume(source, 36) == source.packets


@pytest.mark.capture
def test_all_raw_codes_preserve_every_bit_outside_masks_and_keep_keys_and_samples(states):
    source = states[2]
    before = pattern_data(source, 1)
    for value in range(64):
        after = native(set_calibrated_sound3_volume(source, value))
        assert calibrated_sound3_volumes(after) == (value,) * 16
        data = bytearray(pattern_data(after, 1))
        for step in range(16):
            p = 48 * step + 6
            data[p] = (data[p] & 63) | (before[p] & 192)
            data[p + 1] = (data[p + 1] & 240) | (before[p + 1] & 15)
        assert bytes(data) == before
        assert tuple(p for p in source.packets if p.tag != 0xC498) == tuple(
            p for p in after.packets if p.tag != 0xC498
        )
        assert all(pattern_data(source, slot) == pattern_data(after, slot) for slot in range(2, 17))


@pytest.mark.capture
def test_retained_middle_ramp_is_read_literally_and_can_be_set_uniformly(states):
    root, _, _ = states
    path = (
        root
        / "experiments/event-048-e-sound3-volume-lock-middle/derived/analysis-001/capture.symbols.npz"
    )
    source = decode_artifact(load_artifact(path))
    assert calibrated_sound3_volumes(source) == (
        37,
        41,
        44,
        47,
        47,
        47,
        47,
        46,
        46,
        46,
        46,
        46,
        46,
        46,
        46,
        46,
    )
    target = decode_artifact(
        load_artifact(
            root / "experiments/edited-sound3-volume18-001/derived/analysis-001/capture.symbols.npz"
        )
    )
    assert encode_packets(set_calibrated_sound3_volume(source, 18)) == target.encoded_body


@pytest.mark.capture
@pytest.mark.parametrize("value", [True, False, -1, 64, 255, 21.0, "21", None])
def test_invalid_target_type_or_range_rejected(states, value):
    with pytest.raises(ValueError, match="integer from 0 to 63"):
        set_calibrated_sound3_volume(states[2], value)


@pytest.mark.capture
@pytest.mark.parametrize("offset,mask", [(6, 1), (7, 16), (8, 1), (770, 1), (102, 1)])
def test_unknown_pitch_parameters_keys_or_note_layout_rejected(states, offset, mask):
    source = states[2]
    data = bytearray(pattern_data(source, 1))
    data[offset] ^= mask
    bad = native(_replace_pattern_data(source, 1, bytes(data)))
    with pytest.raises(ValueError, match="Unknown Sound3"):
        set_calibrated_sound3_volume(bad, 21)


@pytest.mark.capture
def test_unknown_window_rejected_and_other_sound_bytes_preserved_literally(states):
    source = states[2]
    packets = list(source.packets)
    index = sound_groups(source)[2][0]
    data = bytearray(packets[index].payload)
    data[4:8] = (19000).to_bytes(4, "little")
    packets[index] = Packet(packets[index].tag, bytes(data))
    with pytest.raises(ValueError, match="tested Sound3 window"):
        set_calibrated_sound3_volume(native(packets), 21)
    data = bytearray(pattern_data(source, 1))
    data[3] ^= 1  # Opaque Sound2 cell, outside this writer's scope.
    opaque = native(_replace_pattern_data(source, 1, bytes(data)))
    result = native(set_calibrated_sound3_volume(opaque, 21))
    assert pattern_data(result, 1)[3:6] == bytes(data[3:6])


def plan_for(path, value):
    frame = decode_artifact(load_artifact(path))
    return {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(path),
        "source_body_sha256": hashlib.sha256(frame.encoded_body).hexdigest(),
        "operations": [{"operation": "set_sound3_volume", "value": value}],
    }


@pytest.mark.capture
@pytest.mark.parametrize(
    "value,name,registration_file",
    [
        (18, "edited-sound3-volume18-001", "sound3-generated-volume18-pair-registration-001.json"),
        (36, "edited-sound3-volume36-002", "sound3-generated-volume36-registration-002.json"),
    ],
)
def test_public_compiler_replays_both_accepted_wavs_byte_for_byte(
    states, tmp_path, value, name, registration_file
):
    root = states[0]
    registration = json.loads((root / "experiments" / registration_file).read_text())
    path = root / registration["source_artifact"]
    before = path.read_bytes()
    plan_path = tmp_path / "plan.json"
    plan_path.write_bytes(json_bytes(plan_for(path, value)))
    output = tmp_path / "compiled"
    report = compile_edit_plan(path, plan_path, output)
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments" / name / "restore.wav"
    ).read_bytes()
    assert report["passed"] and not report["hardware_verified"]
    assert path.read_bytes() == before


@pytest.mark.capture
def test_bound_plan_rejects_stale_hash_and_unavailable_per_step_arguments(states):
    _, path, _ = states
    artifact = load_artifact(path)
    before = artifact.to_bytes()
    plan = plan_for(path, 21)
    with pytest.raises(ValueError, match="source artifact hash"):
        apply_plan(artifact, "0" * 64, plan)
    plan["operations"][0]["step"] = 2
    with pytest.raises(ValueError, match="Unexpected or missing"):
        apply_plan(artifact, sha256_file(path), plan)
    assert artifact.to_bytes() == before
