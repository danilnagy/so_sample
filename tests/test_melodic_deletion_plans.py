"""Replay both observed deletion contexts and reject unverified ownership/event layouts."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.edits import apply_plan
from po33_re.formats.lifecycle import delete_calibrated_melodic_sound
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_data,
    sound_groups,
)
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_unshared_sound7_deletion import comparison_checks


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    last = root / "experiments/event-027-b-delete-unshared-sound7"
    if not (last / "capture.wav").exists():
        pytest.skip("Actual last-owner deletion capture required")
    assert (
        sha256_file(last / "capture.wav")
        == "29658f8c814a9babcfe859316a8e9313e4a6e1ef31f7d7ce2d4d4c2e56e55412"
    )
    empty = decode_artifact(decode_wav(last / "capture.wav", 0.0063))
    shared = decode_artifact(
        load_artifact(
            root / "experiments/edited-sound6-to7-copy-001/derived/analysis-001/capture.symbols.npz"
        )
    )
    transferred = decode_artifact(
        load_artifact(
            root
            / "experiments/event-026-b-delete-shared-sound6/derived/analysis-001/capture.symbols.npz"
        )
    )
    return root, shared, transferred, empty


@pytest.mark.capture
def test_real_last_owner_deletion_clears_record_and_recovers_entire_earlier_state(states):
    root, _, before, actual = states
    reg = json.loads(
        (root / "experiments/unshared-sound7-deletion-predictions-001.json").read_text()
    )
    checks, fits, _ = comparison_checks(before, actual, reg)
    assert all(checks.values()) and fits["entire_empty_record_model_matches"]
    assert not fits["full_codes_retained_under_owner6"]
    assert not sound_groups(actual)[5] and not sound_groups(actual)[6]


@pytest.mark.capture
def test_both_public_deletion_operations_replay_complete_independent_physical_states(states):
    _, shared, transferred, empty = states
    assert encode_packets(delete_calibrated_melodic_sound(shared, 6)) == transferred.encoded_body
    assert encode_packets(delete_calibrated_melodic_sound(transferred, 7)) == empty.encoded_body
    assert sound_data(shared, 5)[9:] == sound_data(transferred, 6)[9:]


@pytest.mark.capture
def test_composed_copy_transfer_and_clear_plan_preserves_source_and_matches_hardware_state(states):
    root, _, _, empty = states
    path = root / "experiments/edited-sound6-create-001/derived/analysis-001/capture.symbols.npz"
    source = load_artifact(path)
    before = source.to_bytes()
    plan = json.loads(
        (root / "experiments/replay-melodic-copy-delete-cycle-001/plan.json").read_text()
    )
    edited, trace = apply_plan(source, sha256_file(path), plan)
    assert decode_artifact(edited).encoded_body == empty.encoded_body
    assert len(trace) == 3 and source.to_bytes() == before
    assert not edited.metadata["hardware_verified"]


@pytest.mark.capture
def test_cycle_compiler_replays_prior_hardware_accepted_wav_byte_exact(states, tmp_path):
    root = states[0]
    output = tmp_path / "cycle"
    source = root / "experiments/edited-sound6-create-001/derived/analysis-001/capture.symbols.npz"
    plan = root / "experiments/replay-melodic-copy-delete-cycle-001/plan.json"
    assert main(["apply-edits", str(source), "--plan", str(plan), "--out-dir", str(output)]) == 0
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments/edited-sound4-shrink-001/restore.wav"
    ).read_bytes()
    report = json.loads((output / "compile-report.json").read_text())
    assert report["passed"] and not report["hardware_verified"]


@pytest.mark.capture
@pytest.mark.parametrize("slot", [True, 1, 4, 8, "6"])
def test_unknown_deletion_slots_and_bools_fail(states, slot):
    with pytest.raises(ValueError):
        delete_calibrated_melodic_sound(states[1], slot)


@pytest.mark.capture
def test_extra_referrer_wrong_retained_window_and_unverified_note_are_rejected(states):
    _, shared, _, _ = states
    packets = list(shared.packets)
    index = sound_groups(shared)[7][0]
    packets[index] = Packet(0xEF78, sound_data(shared, 5)[:9])
    with pytest.raises(ValueError, match="retained"):
        delete_calibrated_melodic_sound(native(packets), 6)
    packets = list(shared.packets)
    index = sound_groups(shared)[6][0]
    data = packets[index].payload
    packets[index] = Packet(0xEF78, data[:4] + (30913).to_bytes(4, "little") + data[8:])
    with pytest.raises(ValueError, match="retained"):
        delete_calibrated_melodic_sound(native(packets), 6)
    pattern = bytearray(pattern_data(shared, 1))
    pattern[15:18] = bytes.fromhex("0df883")
    pattern[773] = 240
    with pytest.raises(ValueError, match="events"):
        delete_calibrated_melodic_sound(native(_replace_pattern_data(shared, 1, bytes(pattern))), 6)


@pytest.mark.capture
def test_unshared_delete_rejects_new_alias_and_packetization_outside_observation(states):
    _, shared, transferred, _ = states
    packets = list(transferred.packets)
    index = sound_groups(transferred)[7][0]
    packets[index] = Packet(0xEF78, sound_data(transferred, 6)[:9])
    with pytest.raises(ValueError, match="unshared"):
        delete_calibrated_melodic_sound(native(packets), 7)
    packets = list(shared.packets)
    a, b = sound_groups(shared)[5][15:17]
    left, right = packets[a].payload, packets[b].payload
    packets[a], packets[b] = Packet(0xEF78, left[:-1]), Packet(0xEF78, left[-1:] + right)
    with pytest.raises(ValueError, match="geometry"):
        delete_calibrated_melodic_sound(native(packets), 6)
