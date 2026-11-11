"""Replay verified tempo states and reject unobserved opaque contexts and values."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.edits import apply_plan
from po33_re.formats.globals import calibrated_tempo_preset, set_calibrated_tempo_preset
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo80_restore import restore_checks
from scripts.check_tempo_control import comparison_checks


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-tempo80-001"
    if not (directory / "hardware-acceptance-001.json").exists():
        pytest.skip("Accepted generated tempo restore required")
    acceptance = json.loads((directory / "hardware-acceptance-001.json").read_text())
    actual_path = root / acceptance["artifact_path"]
    assert acceptance["hardware_verified"] and all(acceptance["checks"].values())
    assert sha256_file(actual_path) == acceptance["artifact_sha256"]
    assert (
        sha256_file(directory / "capture.wav")
        == "7512efa7fa484824a6e68a2747bb3d4a4a44f031ca02259728248e47e59465f6"
    )
    reg = json.loads((directory / "restore-registration.json").read_text())
    source_path = root / reg["baseline_artifact"]
    actual = decode_artifact(load_artifact(actual_path))
    original = decode_artifact(load_artifact(source_path))
    genuine = decode_artifact(load_artifact(root / reg["genuine80_artifact"]))
    tempo140 = decode_artifact(
        load_artifact(
            root
            / "experiments/event-030-b-tempo-preset-once/derived/analysis-001/capture.symbols.npz"
        )
    )
    return root, source_path, original, actual, genuine, tempo140, reg


@pytest.mark.capture
def test_actual_generated_restore_matches_independent_genuine80_and_all_controls(states):
    _, _, base, actual, genuine, _, reg = states
    controls, fits, exact, _ = restore_checks(base, actual, actual, genuine, reg, 80)
    assert all(controls.values()) and all(fits.values()) and all(exact.values())


@pytest.mark.capture
def test_public_presets_reproduce_complete_independent_physical_states_and_noop(states):
    _, _, original, actual, _, tempo140, _ = states
    assert calibrated_tempo_preset(actual) == 80
    assert calibrated_tempo_preset(original) == 120
    assert calibrated_tempo_preset(tempo140) == 140
    assert encode_packets(set_calibrated_tempo_preset(original, 80)) == actual.encoded_body
    assert encode_packets(set_calibrated_tempo_preset(actual, 120)) == original.encoded_body
    assert encode_packets(set_calibrated_tempo_preset(actual, 140)) == tempo140.encoded_body
    assert set_calibrated_tempo_preset(actual, 80) == actual.packets


@pytest.mark.capture
def test_plan_compiler_exactly_replays_hardware_accepted_wav_and_refuses_overwrite(
    states, tmp_path
):
    root, source_path, _, actual, _, _, _ = states
    plan_path = root / "experiments/replay-tempo80-preset-plan-001/plan.json"
    output = tmp_path / "compiled"
    before = source_path.read_bytes()
    args = ["apply-edits", str(source_path), "--plan", str(plan_path), "--out-dir", str(output)]
    assert main(args) == 0
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments/edited-tempo80-001/restore.wav"
    ).read_bytes()
    assert (
        decode_artifact(load_artifact(output / "edited.symbols.npz")).encoded_body
        == actual.encoded_body
    )
    report = json.loads((output / "compile-report.json").read_text())
    assert report["passed"] and not report["hardware_verified"]
    assert source_path.read_bytes() == before and main(args) == 2


@pytest.mark.capture
@pytest.mark.parametrize("value", [True, False, 100, 60, 240, 256, "80", 80.0, None])
def test_preset_target_does_not_expand_to_arbitrary_values_or_bools(states, value):
    with pytest.raises(ValueError, match="Tempo preset"):
        set_calibrated_tempo_preset(states[3], value)


@pytest.mark.capture
@pytest.mark.parametrize("index,offset", [(1, 0), (2, 128), (2, 131), (2, 254)])
def test_unknown_opaque_global_bytes_are_rejected_instead_of_silently_reset(states, index, offset):
    packets = list(states[3].packets)
    data = bytearray(packets[index].payload)
    data[offset] ^= 1
    packets[index] = Packet(0x7D5C, bytes(data))
    with pytest.raises(ValueError, match="Unknown opaque global context"):
        set_calibrated_tempo_preset(native(packets), 120)


@pytest.mark.capture
def test_unobserved_fine_tempo_source_and_global_record_geometry_are_rejected(states):
    packets = list(states[3].packets)
    old = packets[2].payload
    packets[2] = Packet(0x7D5C, old[:129] + b"\x64" + old[130:])
    with pytest.raises(ValueError, match="Source tempo"):
        set_calibrated_tempo_preset(native(packets), 80)
    packets[2] = Packet(0x7D5C, old[:-1])
    with pytest.raises(ValueError, match="two-global-record layout"):
        set_calibrated_tempo_preset(native(packets), 120)
    packets = list(states[3].packets)
    packets.insert(3, Packet(0x7D5C, bytes(255)))
    with pytest.raises(ValueError, match="two-global-record layout"):
        set_calibrated_tempo_preset(native(packets), 120)


@pytest.mark.capture
def test_changed_sample_content_is_preserved_while_setting_a_calibrated_global_preset(states):
    _, _, _, actual, _, _, _ = states
    packets = list(actual.packets)
    index = sound_groups(actual)[0][1]
    data = bytearray(packets[index].payload)
    data[27] ^= 1
    packets[index] = Packet(0xEF78, bytes(data))
    source = native(packets)
    changed = set_calibrated_tempo_preset(source, 140)
    assert changed[index] == packets[index]
    assert tuple(p for p in changed if p.tag != 0x7D5C) == tuple(
        p for p in source.packets if p.tag != 0x7D5C
    )


@pytest.mark.capture
def test_hash_bound_preset_plan_rejects_the_current_different_source(states):
    root, source_path, _, _, _, _, _ = states
    plan = json.loads((root / "experiments/replay-tempo80-preset-plan-001/plan.json").read_text())
    source = load_artifact(source_path)
    edited, trace = apply_plan(source, sha256_file(source_path), plan)
    assert len(trace) == 1 and not edited.metadata["hardware_verified"]
    current_path = root / "experiments/edited-tempo80-001/derived/analysis-001/capture.symbols.npz"
    with pytest.raises(ValueError, match="source artifact hash"):
        apply_plan(load_artifact(current_path), sha256_file(current_path), plan)


@pytest.mark.capture
def test_fine100_model_passes_prediction_checks_but_remains_outside_public_preset_scope(states):
    root, _, _, actual, _, _, _ = states
    directory = root / "experiments/event-033-b-fine-tempo-100"
    registration = json.loads((directory / "tempo-registration.json").read_text())
    predicted = decode_frame(bytes(4095) + (directory / "predicted-native-body.bin").read_bytes())
    controls, fits, _ = comparison_checks(actual, predicted, registration, 80, 100)
    assert all(controls.values()) and all(fits.values())
    with pytest.raises(ValueError, match="Source tempo"):
        calibrated_tempo_preset(predicted)
