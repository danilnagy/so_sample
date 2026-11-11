"""Public observed-code FILTER plans preserve opaque state and replay accepted bodies/WAVs."""

import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import json_bytes, sha256_file
from po33_re.edits import apply_plan, compile_edit_plan
from po33_re.formats.filters import calibrated_sound3_filters, set_calibrated_sound3_filter
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-generated-filter16-52-registration-001.json"
    if not path.exists():
        pytest.skip("FILTER evidence required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    folders = {
        1: "event-056-c-sound3-filter-A-lock-down",
        16: "edited-sound3-filter16-lowpass-001",
        52: "edited-sound3-filter52-highpass-001",
        62: "event-057-d-return-sound3-filter-A-lock-up",
        63: "event-061-h-return-sound3-filter-A-center",
    }
    frames = {}
    for value, name in folders.items():
        observation = json.loads(
            (root / "experiments" / name / "hardware-observation-001.json").read_text()
        )
        assert observation["hardware_verified"] and all(observation["checks"].values())
        artifact_path = root / observation["artifact_path"]
        assert sha256_file(artifact_path) == observation["artifact_sha256"]
        frames[value] = decode_artifact(load_artifact(artifact_path))
    return root, source_path, frames, registration


@pytest.mark.capture
@pytest.mark.parametrize("source_value", [1, 16, 52, 62, 63])
def test_every_supported_source_reconstructs_each_entire_independent_body(states, source_value):
    frames = states[2]
    for value, independent in frames.items():
        assert calibrated_sound3_filters(independent) == (value,) * 16
        assert (
            encode_packets(set_calibrated_sound3_filter(frames[source_value], value))
            == independent.encoded_body
        )
    assert (
        set_calibrated_sound3_filter(frames[source_value], source_value)
        == frames[source_value].packets
    )


@pytest.mark.capture
def test_unwritten_zero_is_accepted_only_in_parameter_cells_and_other_state_is_preserved(states):
    root, _, frames, _ = states
    source = decode_artifact(
        load_artifact(
            root
            / "experiments/event-054-a-sound3-filter-selection/derived/analysis-001/capture.symbols.npz"
        )
    )
    values = calibrated_sound3_filters(source)
    assert values.count(0) == 11 and values.count(63) == 5
    assert encode_packets(set_calibrated_sound3_filter(source, 52)) == frames[52].encoded_body
    data = bytearray(pattern_data(frames[63], 1))
    data[3] ^= 1
    neighbor = native(_replace_pattern_data(frames[63], 1, bytes(data)))
    target = native(set_calibrated_sound3_filter(neighbor, 16))
    assert pattern_data(target, 1)[3:6] == bytes(data[3:6])


@pytest.mark.capture
@pytest.mark.parametrize(
    "value", [True, False, 0, -1, 2, 15, 17, 31, 32, 51, 53, 61, 64, 16.0, "52", None]
)
def test_unsupported_target_codes_and_types_fail(states, value):
    with pytest.raises(ValueError, match="integer in"):
        set_calibrated_sound3_filter(states[2][52], value)


@pytest.mark.capture
@pytest.mark.parametrize(
    "damage",
    [
        "bit5",
        "pitch",
        "volume",
        "opaque_note",
        "opaque_parameter",
        "key",
        "new_note",
        "note_zero",
        "source32",
    ],
)
def test_unknown_source_context_is_rejected(states, damage):
    base = states[2][63]
    data = bytearray(pattern_data(base, 1))
    if damage in ("note_zero", "source32"):
        value = 0 if damage == "note_zero" else 32
        data[7] = (data[7] & 15) | ((value & 15) << 4)
        data[8] = (data[8] & 252) | (value >> 4)
    else:
        offset, mask = {
            "bit5": (6, 32),
            "pitch": (6, 1),
            "volume": (7, 1),
            "opaque_note": (8, 4),
            "opaque_parameter": (56, 128),
            "key": (770, 1),
            "new_note": (786, 1),
        }[damage]
        data[offset] ^= mask
    bad = native(_replace_pattern_data(base, 1, bytes(data)))
    with pytest.raises(ValueError, match="Unknown Sound3 filter context"):
        set_calibrated_sound3_filter(bad, 16)


@pytest.mark.capture
def test_unknown_sample_window_is_rejected(states):
    base = states[2][52]
    packets = list(base.packets)
    index = sound_groups(base)[2][0]
    data = bytearray(packets[index].payload)
    data[4:8] = (19000).to_bytes(4, "little")
    packets[index] = Packet(packets[index].tag, bytes(data))
    with pytest.raises(ValueError, match="tested Sound3 window"):
        set_calibrated_sound3_filter(native(packets), 63)


def plan_for(path, value):
    source = decode_artifact(load_artifact(path))
    return {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(path),
        "source_body_sha256": hashlib.sha256(source.encoded_body).hexdigest(),
        "operations": [{"operation": "set_sound3_filter", "value": value}],
    }


@pytest.mark.capture
@pytest.mark.parametrize("index", [0, 1])
def test_public_plans_replay_both_accepted_restore_wavs_byte_for_byte(states, tmp_path, index):
    root, path, _, registration = states
    leg = registration["expected_capture_sequence"][index]
    before = path.read_bytes()
    plan_path = tmp_path / "plan.json"
    plan_path.write_bytes(json_bytes(plan_for(path, leg["raw_filter_value"])))
    output = tmp_path / "compiled"
    report = compile_edit_plan(path, plan_path, output)
    assert report["passed"] and not report["hardware_verified"]
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments" / leg["experiment_id"] / "restore.wav"
    ).read_bytes()
    assert path.read_bytes() == before


@pytest.mark.capture
def test_stale_hashes_and_extra_arguments_cannot_bypass_guards(states):
    path = states[1]
    source = load_artifact(path)
    before = source.to_bytes()
    plan = plan_for(path, 16)
    with pytest.raises(ValueError, match="source artifact hash"):
        apply_plan(source, "0" * 64, plan)
    plan["source_body_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source native-body hash"):
        apply_plan(source, sha256_file(path), plan)
    plan = plan_for(path, 16)
    plan["operations"][0]["step"] = 1
    with pytest.raises(ValueError, match="Unexpected or missing"):
        apply_plan(source, sha256_file(path), plan)
    assert source.to_bytes() == before
