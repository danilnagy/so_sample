"""Replay hardware-supported fine tempo and preserve unresolved swing hypotheses."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.formats.globals import calibrated_tempo, calibrated_tempo_preset, set_calibrated_tempo
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.symbols import load_artifact
from scripts.check_swing_max_control import comparison_checks as swing_checks


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-fine-tempo137-001"
    if not (directory / "hardware-acceptance-001.json").exists():
        pytest.skip("Accepted generated fine137 restore required")
    acceptance = json.loads((directory / "hardware-acceptance-001.json").read_text())
    assert acceptance["hardware_verified"] and acceptance["fine_tempo_writer_verified"]
    path = root / acceptance["artifact_path"]
    assert sha256_file(path) == acceptance["artifact_sha256"]
    assert (
        sha256_file(directory / "capture.wav")
        == "0538c163106bac0f0c9ac88471ab246c3c53dc713db60c86233eed68e87e9a13"
    )
    current = decode_artifact(load_artifact(path))
    source_reg = json.loads((directory / "restore-registration.json").read_text())
    before_path = root / source_reg["baseline_artifact"]
    before = decode_artifact(load_artifact(before_path))
    swing_reg = json.loads(
        (root / "experiments/event-037-b-swing-maximum/swing-registration.json").read_text()
    )
    return root, before_path, before, current, swing_reg


@pytest.mark.capture
def test_general_tempo_reproduces_generated137_and_all_independent_physical_values(states):
    root, _, before, current, _ = states
    assert encode_packets(set_calibrated_tempo(before, 137)) == current.encoded_body
    assert calibrated_tempo(current) == 137
    assert set_calibrated_tempo(current, 137) == current.packets
    paths = {
        60: "event-034-b-fine-tempo-60",
        240: "event-035-c-fine-tempo-240",
        100: "event-036-a-return-fine-tempo-100",
        80: "event-031-b-tempo-80",
        120: "event-032-a-return-tempo-120",
        140: "event-030-b-tempo-preset-once",
    }
    for bpm, name in paths.items():
        genuine = decode_artifact(
            load_artifact(root / "experiments" / name / "derived/analysis-001/capture.symbols.npz")
        )
        assert calibrated_tempo(genuine) == bpm
        assert encode_packets(set_calibrated_tempo(current, bpm)) == genuine.encoded_body


@pytest.mark.capture
def test_fine_tempo_plan_compiler_replays_accepted_wav_without_mutating_source(states, tmp_path):
    root, path, _, current, _ = states
    plan_path = root / "experiments/replay-fine-tempo137-plan-001/plan.json"
    output = tmp_path / "compiled"
    original_bytes = path.read_bytes()
    args = ["apply-edits", str(path), "--plan", str(plan_path), "--out-dir", str(output)]
    assert main(args) == 0
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments/edited-fine-tempo137-001/restore.wav"
    ).read_bytes()
    assert (
        decode_artifact(load_artifact(output / "edited.symbols.npz")).encoded_body
        == current.encoded_body
    )
    assert not json.loads((output / "compile-report.json").read_text())["hardware_verified"]
    assert path.read_bytes() == original_bytes and main(args) == 2


@pytest.mark.capture
@pytest.mark.parametrize("value", [True, False, 59, 241, 256, "137", 137.0, None])
def test_general_tempo_rejects_out_of_range_targets_and_noninteger_values(states, value):
    with pytest.raises(ValueError, match="integer from 60 to 240"):
        set_calibrated_tempo(states[3], value)


@pytest.mark.capture
@pytest.mark.parametrize("value", [0, 59, 241, 255])
def test_source_outside_observed_tempo_limits_is_rejected(states, value):
    packets = list(states[3].packets)
    old = packets[2].payload
    packets[2] = Packet(0x7D5C, old[:129] + bytes([value]) + old[130:])
    with pytest.raises(ValueError, match="Source tempo"):
        set_calibrated_tempo(native(packets), 137)


@pytest.mark.capture
def test_unknown_swing_context_is_not_reset_by_general_tempo_edit(states):
    packets = list(states[3].packets)
    data = bytearray(packets[2].payload)
    data[130] = 99
    packets[2] = Packet(0x7D5C, bytes(data))
    with pytest.raises(ValueError, match="Unknown opaque global context"):
        set_calibrated_tempo(native(packets), 120)
    with pytest.raises(ValueError, match="three calibrated presets"):
        calibrated_tempo_preset(states[3])


@pytest.mark.capture
def test_swing_candidate_change_keeps_tempo_and_does_not_assume_units(states):
    _, _, _, base, reg = states
    packets = list(base.packets)
    data = bytearray(packets[2].payload)
    data[130] = 99  # Synthetic candidate; not a predicted device maximum.
    packets[2] = Packet(0x7D5C, bytes(data))
    controls, fits, observed = swing_checks(base, native(packets), reg)
    assert all(controls.values()) and fits["only_registered_swing_candidate_byte_changed"]
    assert fits["candidate_equals_independently_reported_display_value"] is None
    assert observed["display_value"] is None and not observed["numeric_swing_encoding_confirmed"]


@pytest.mark.capture
def test_swing_display_mismatch_or_changed_other_offset_is_reported_without_fitting(states):
    _, _, _, base, reg = states
    packets = list(base.packets)
    data = bytearray(packets[2].payload)
    data[130] = 99
    packets[2] = Packet(0x7D5C, bytes(data))
    _, fits, observed = swing_checks(base, native(packets), reg, 100, "SW100")
    assert not fits["candidate_equals_independently_reported_display_value"]
    assert observed["display_text"] == "SW100"
    data[130], data[131] = 0, 99
    packets[2] = Packet(0x7D5C, bytes(data))
    controls, fits, observed = swing_checks(base, native(packets), reg, 99)
    assert all(controls.values()) and not fits["only_registered_swing_candidate_byte_changed"]
    assert observed["candidate_changed_offsets"] == [131]


@pytest.mark.capture
def test_swing_control_rejects_tempo_change_and_allows_valid_no_serialized_change(states):
    _, _, _, base, reg = states
    controls, fits, _ = swing_checks(base, base, reg)
    assert all(controls.values()) and not fits["native_body_changed"]
    packets = set_calibrated_tempo(base, 140)
    controls, _, _ = swing_checks(base, native(packets), reg)
    assert not controls["tempo137_preserved"]
