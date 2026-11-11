"""Public raw pitch editing must reproduce accepted controls and reject unknown context."""

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
from po33_re.formats.pitch import calibrated_sound3_pitches, set_calibrated_sound3_pitch
from po33_re.modem.symbols import load_artifact


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-sound3-pitch14-001"
    observation_path = folder / "hardware-observation-001.json"
    if not observation_path.exists():
        pytest.skip("Physical generated14 interval evidence required")
    observation = json.loads(observation_path.read_text())
    assert observation["hardware_verified"] and all(observation["checks"].values())
    path = root / observation["artifact_path"]
    assert sha256_file(path) == observation["artifact_sha256"]
    return root, path, decode_artifact(load_artifact(path))


@pytest.mark.capture
def test_public_pitch_reconstructs_entire_independent_endpoint_and_interior_bodies(states):
    root, _, source = states
    for value, name in (
        (1, "event-051-b-sound3-tone-pitch-lock-down"),
        (25, "event-052-c-sound3-tone-pitch-lock-up"),
        (13, "edited-sound3-pitch13-reference-001"),
        (14, "edited-sound3-pitch14-001"),
    ):
        genuine = decode_artifact(
            load_artifact(root / "experiments" / name / "derived/analysis-001/capture.symbols.npz")
        )
        assert calibrated_sound3_pitches(genuine) == (value,) * 16
        assert encode_packets(set_calibrated_sound3_pitch(source, value)) == genuine.encoded_body
    assert set_calibrated_sound3_pitch(source, 14) == source.packets


@pytest.mark.capture
def test_all_supported_raw_codes_preserve_every_nonpitch_bit_sample_and_key(states):
    source = states[2]
    before = pattern_data(source, 1)
    for value in range(1, 26):
        target = native(set_calibrated_sound3_pitch(source, value))
        assert calibrated_sound3_pitches(target) == (value,) * 16
        data = bytearray(pattern_data(target, 1))
        for step in range(16):
            p = 48 * step + 6
            data[p] = (data[p] & 224) | (before[p] & 31)
        assert bytes(data) == before
        assert tuple(p for p in source.packets if p.tag != 0xC498) == tuple(
            p for p in target.packets if p.tag != 0xC498
        )
        assert all(
            pattern_data(source, slot) == pattern_data(target, slot) for slot in range(2, 17)
        )


@pytest.mark.capture
def test_original_parameter_only_zero_is_read_literally_then_written_uniformly(states):
    root = states[0]
    original = decode_artifact(
        load_artifact(
            root / "experiments/edited-sound3-volume36-002/derived/analysis-001/capture.symbols.npz"
        )
    )
    assert calibrated_sound3_pitches(original) == (
        13,
        13,
        0,
        0,
        13,
        0,
        0,
        0,
        13,
        0,
        0,
        0,
        13,
        0,
        0,
        0,
    )
    assert encode_packets(set_calibrated_sound3_pitch(original, 14)) == states[2].encoded_body


@pytest.mark.capture
@pytest.mark.parametrize("value", [True, False, 0, -1, 26, 63, 14.0, "14", None])
def test_invalid_target_types_and_codes_rejected(states, value):
    with pytest.raises(ValueError, match="integer from 1 to 25"):
        set_calibrated_sound3_pitch(states[2], value)


@pytest.mark.capture
@pytest.mark.parametrize(
    "damage",
    [
        "bit5",
        "note_zero",
        "source26",
        "volume",
        "second_parameter",
        "third_parameter",
        "key",
        "new_note",
    ],
)
def test_unknown_bits_pitch_range_volume_or_note_parameters_rejected(states, damage):
    source = states[2]
    data = bytearray(pattern_data(source, 1))
    if damage == "note_zero":
        data[6] &= 224
    elif damage == "source26":
        data[6] = (data[6] & 224) | 26
    else:
        offset, mask = {
            "bit5": (6, 32),
            "volume": (6, 64),
            "second_parameter": (7, 16),
            "third_parameter": (8, 1),
            "key": (770, 1),
            "new_note": (104, 1),
        }[damage]
        data[offset] ^= mask
    bad = native(_replace_pattern_data(source, 1, bytes(data)))
    with pytest.raises(ValueError, match="Unknown Sound3 pitch context"):
        set_calibrated_sound3_pitch(bad, 13)


@pytest.mark.capture
def test_unknown_window_rejected_and_neighbor_data_preserved(states):
    source = states[2]
    packets = list(source.packets)
    index = sound_groups(source)[2][0]
    data = bytearray(packets[index].payload)
    data[4:8] = (19000).to_bytes(4, "little")
    packets[index] = Packet(packets[index].tag, bytes(data))
    with pytest.raises(ValueError, match="tested Sound3 window"):
        set_calibrated_sound3_pitch(native(packets), 13)
    data = bytearray(pattern_data(source, 1))
    data[3] ^= 1
    opaque = native(_replace_pattern_data(source, 1, bytes(data)))
    target = native(set_calibrated_sound3_pitch(opaque, 13))
    assert pattern_data(target, 1)[3:6] == bytes(data[3:6])


def plan_for(path, value):
    source = decode_artifact(load_artifact(path))
    return {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(path),
        "source_body_sha256": hashlib.sha256(source.encoded_body).hexdigest(),
        "operations": [{"operation": "set_sound3_pitch", "value": value}],
    }


@pytest.mark.capture
@pytest.mark.parametrize(
    "value,name", [(13, "edited-sound3-pitch13-reference-001"), (14, "edited-sound3-pitch14-001")]
)
def test_public_compiler_replays_both_accepted_pitch_wavs_byte_for_byte(
    states, tmp_path, value, name
):
    root = states[0]
    registration = json.loads(
        (root / "experiments/sound3-generated-pitch13-14-registration-001.json").read_text()
    )
    path = root / registration["source_artifact"]
    before = path.read_bytes()
    plan_path = tmp_path / "plan.json"
    plan_path.write_bytes(json_bytes(plan_for(path, value)))
    output = tmp_path / "compiled"
    report = compile_edit_plan(path, plan_path, output)
    assert report["passed"] and not report["hardware_verified"]
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments" / name / "restore.wav"
    ).read_bytes()
    assert path.read_bytes() == before


@pytest.mark.capture
def test_source_hash_and_unavailable_per_step_arguments_cannot_bypass_guards(states):
    path = states[1]
    source = load_artifact(path)
    before = source.to_bytes()
    plan = plan_for(path, 13)
    with pytest.raises(ValueError, match="source artifact hash"):
        apply_plan(source, "0" * 64, plan)
    plan["operations"][0]["step"] = 2
    with pytest.raises(ValueError, match="Unexpected or missing"):
        apply_plan(source, sha256_file(path), plan)
    assert source.to_bytes() == before
