"""Verify cell-copy preservation and keep failed raw-field hypotheses visible."""

import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.formats.packets import (
    END_TAG,
    START_TAG,
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
)
from po33_re.formats.patterns import clone_sound_cell, pattern_data, remove_sound_cell
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_sound_add_control import comparison_checks
from scripts.validate_sound_cell_recapture import comparison_checks as recapture_checks
from scripts.validate_sound_cell_removal_recapture import (
    comparison_checks as removal_recapture_checks,
)


def cell_frame(damage=None, with_sound2=True):
    pattern = bytearray(1024) + bytes([255]) * 8
    if with_sound2:
        pattern[3:6], pattern[769] = bytes.fromhex("0d2831"), 240
    for step, key in ((1, 1), (5, 2), (9, 7), (13, 16)):
        p, a = 48 * (step - 1), 768 + 16 * (step - 1)
        pattern[p + 6 : p + 9], pattern[a + 2] = bytes.fromhex("0df883"), 240 | (key - 1)
    if damage == "source_primary":
        pattern[4] ^= 1
    elif damage == "source_auxiliary":
        pattern[769] = 241
    elif damage == "source_neighbor":
        pattern[7] ^= 1
    elif damage == "unmatched_source":
        pattern[770] = 0
    elif damage == "occupied_target_primary":
        pattern[387] = 1
    elif damage == "occupied_target_auxiliary":
        pattern[897] = 240
    elif damage == "unknown_target_neighbor":
        pattern[390:393] = bytes.fromhex("0df884")
    elif damage == "extra_cell":
        pattern[9:12], pattern[771] = bytes.fromhex("010203"), 240
    elif damage == "source_primary_empty":
        pattern[3:6] = bytes(3)
    elif damage == "source_auxiliary_empty":
        pattern[769] = 0
    packets = [Packet(START_TAG, b"")]
    for slot in range(16):
        packets.append(Packet(0xA041, bytes([slot])))
        data = bytes(pattern) if slot == 0 else bytes(1024) + bytes([255]) * 8
        packets.extend(Packet(0xC498, data[i : i + 255]) for i in range(0, 1032, 255))
    packets.append(Packet(END_TAG, b""))
    return decode_frame(encode_packets(packets), start=0)


def test_copy_changes_only_sound2_cells_and_preserves_neighbors_across_chunks():
    frame = cell_frame()
    unchanged = encode_packets(frame.packets)
    before = pattern_data(frame, 1)
    copied = decode_frame(encode_packets(clone_sound_cell(frame, 1, 2, 1, [5, 9, 16])), start=0)
    expected = bytearray(before)
    for step in (5, 9, 16):
        p, a = 48 * (step - 1), 768 + 16 * (step - 1)
        expected[p + 3 : p + 6], expected[a + 1] = bytes.fromhex("0d2831"), 240
    assert pattern_data(copied, 1) == bytes(expected)
    assert encode_packets(frame.packets) == unchanged
    assert len(frame.packets) == len(copied.packets)
    assert all(
        a.tag == b.tag and len(a.payload) == len(b.payload)
        for a, b in zip(frame.packets, copied.packets)
    )
    assert all(pattern_data(frame, p) == pattern_data(copied, p) for p in range(2, 17))


@pytest.mark.parametrize(
    "source,targets,sound",
    [
        (0, [9], 2),
        (1, [], 2),
        (1, [0], 2),
        (1, [17], 2),
        (1, [True], 2),
        (1, [9, 9], 2),
        (1, [1], 2),
        (5, [9], 2),
        (1, [9], 3),
    ],
)
def test_cell_copy_rejects_invalid_or_unobserved_source_and_destination(source, targets, sound):
    with pytest.raises(ValueError):
        clone_sound_cell(cell_frame(), 1, sound, source, targets)


@pytest.mark.parametrize(
    "damage",
    [
        "source_primary",
        "source_auxiliary",
        "source_neighbor",
        "unmatched_source",
        "occupied_target_primary",
        "occupied_target_auxiliary",
        "unknown_target_neighbor",
        "extra_cell",
    ],
)
def test_cell_copy_rejects_unknown_parameters_and_partial_occupied_cells(damage):
    frame = cell_frame(damage)
    unchanged = encode_packets(frame.packets)
    with pytest.raises(ValueError):
        clone_sound_cell(frame, 1, 2, 1, [5, 9])
    assert encode_packets(frame.packets) == unchanged


def test_preservation_can_pass_while_the_primary_equality_hypothesis_fails():
    root = Path(__file__).resolve().parents[1]
    registration = json.loads((root / "experiments/sound2-layer-predictions-001.json").read_text())
    base, actual = cell_frame(with_sound2=False), cell_frame()
    registration["control_checks"].update(
        packet_count=len(base.packets), frame_end_byte=base.end_byte
    )
    checks, hypotheses, _, changes, slots = comparison_checks(base, actual, registration)
    assert all(checks.values())
    assert hypotheses == {
        "primary_matches_sound3_key1": False,
        "auxiliary_key_index": True,
        "changed_plain_packet_indices": False,  # Synthetic frame omits the two global packets.
    }
    assert [c["offset"] for c in changes] == [3, 4, 5, 769]
    assert slots == [2, 3]


@pytest.mark.capture
def test_genuine_sound2_control_preserves_sound3_and_records_failed_hypothesis():
    root = Path(__file__).resolve().parents[1]
    capture = root / "experiments/event-011-b-sound2-layer/capture.wav"
    base_path = root / "experiments/edited-four-keys-001/derived/analysis-002/capture.symbols.npz"
    if not capture.exists() or not base_path.exists():
        pytest.skip("Genuine four-key baseline and Sound2 addition capture required")
    assert (
        sha256_file(capture) == "34b9b78a92d62e76383ee2bd673ae1590793e10b2376ed2dd19974d8c1d16549"
    )
    base, actual = (
        decode_artifact(load_artifact(base_path)),
        decode_artifact(decode_wav(capture, 0.0063)),
    )
    assert hashlib.sha256(actual.encoded_body).hexdigest() == (
        "e2d6c4a33c045deec30c27449a39182dc6bd0fb80bbe002aba85b0678ce4681d"
    )
    registration = json.loads((root / "experiments/sound2-layer-predictions-001.json").read_text())
    checks, hypotheses, packets, changes, slots = comparison_checks(base, actual, registration)
    assert all(checks.values())
    assert hypotheses["primary_matches_sound3_key1"] is False
    assert hypotheses["auxiliary_key_index"] is True
    assert hypotheses["changed_plain_packet_indices"] is True
    assert packets == [4, 7] and slots == [2, 3]
    assert changes == [
        {"offset": 3, "old": 0, "new": 13},
        {"offset": 4, "old": 0, "new": 40},
        {"offset": 5, "old": 0, "new": 49},
        {"offset": 769, "old": 0, "new": 240},
    ]


@pytest.mark.capture
def test_cell_copy_cli_produces_exact_candidate_and_protects_input(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = root / "experiments/event-011-b-sound2-layer/derived/analysis-001/capture.symbols.npz"
    if not source.exists():
        pytest.skip("Reviewed Sound2 addition artifact required")
    before = source.read_bytes()
    output, report = tmp_path / "cloned.npz", tmp_path / "clone.json"
    args = [
        "clone-sound-cell",
        str(source),
        "--pattern",
        "1",
        "--sound",
        "2",
        "--source-step",
        "1",
        "--target-steps",
        "9",
        "--out",
        str(output),
        "--report",
        str(report),
    ]
    assert main(args) == 0
    result = json.loads(report.read_text())
    assert result["hardware_verified"] is False
    assert result["native_frame"]["encoded_body_sha256"] == (
        "4362aa66f6c18e7351b39016eb1b801dfa4a6ce0f4935861d4aaf45c8737668b"
    )
    assert main(args) == 2
    assert main(args[: args.index("--out")] + ["--out", str(source), "--force"]) == 2
    assert source.read_bytes() == before


def test_removal_preserves_neighbour_and_remaining_copy_then_exactly_reverses():
    original = cell_frame()
    two_notes = decode_frame(encode_packets(clone_sound_cell(original, 1, 2, 1, [9])), start=0)
    unchanged = encode_packets(two_notes.packets)
    removed = decode_frame(encode_packets(remove_sound_cell(two_notes, 1, 2, [1])), start=0)
    before, after = pattern_data(two_notes, 1), pattern_data(removed, 1)
    assert [(i, a, b) for i, (a, b) in enumerate(zip(before, after)) if a != b] == [
        (3, 13, 0),
        (4, 40, 0),
        (5, 49, 0),
        (769, 240, 0),
    ]
    assert encode_packets(clone_sound_cell(removed, 1, 2, 9, [1])) == unchanged
    assert encode_packets(two_notes.packets) == unchanged
    assert (
        encode_packets(remove_sound_cell(two_notes, 1, 2, [1, 9]))
        == cell_frame(with_sound2=False).encoded_body
    )


@pytest.mark.parametrize(
    "steps,sound", [([], 2), ([0], 2), ([17], 2), ([True], 2), ([1, 1], 2), ([5], 2), ([1], 3)]
)
def test_removal_rejects_invalid_empty_or_unsupported_cells(steps, sound):
    with pytest.raises(ValueError):
        remove_sound_cell(cell_frame(), 1, sound, steps)


@pytest.mark.parametrize(
    "damage",
    [
        "source_primary",
        "source_auxiliary",
        "source_neighbor",
        "unmatched_source",
        "extra_cell",
        "source_primary_empty",
        "source_auxiliary_empty",
    ],
)
def test_removal_rejects_unknown_parameters_and_partial_cells_without_mutation(damage):
    original = cell_frame(damage)
    before = encode_packets(original.packets)
    with pytest.raises(ValueError):
        remove_sound_cell(original, 1, 2, [1])
    assert encode_packets(original.packets) == before


@pytest.fixture(scope="module")
def genuine_cell_copy():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-sound2-cell-001"
    capture = directory / "capture.wav"
    paths = [
        root / "experiments/event-011-b-sound2-layer/derived/analysis-001/capture.symbols.npz",
        root / "experiments/generated-sound2-cell-001/edited.symbols.npz",
        root / "experiments/edited-four-keys-001/derived/analysis-002/capture.symbols.npz",
        directory / "restore-registration.json",
    ]
    if not capture.exists() or not all(p.exists() for p in paths):
        pytest.skip(
            "Genuine cell-copy recapture, source, target, four-key baseline and registration required"
        )
    assert (
        sha256_file(capture) == "1adb6964a06f239adfcd599c2996b6d2d075e67576e63955e150ec8c5d84b56f"
    )
    actual = decode_artifact(decode_wav(capture, 0.0063))
    assert (
        hashlib.sha256(actual.encoded_body).hexdigest()
        == "4362aa66f6c18e7351b39016eb1b801dfa4a6ce0f4935861d4aaf45c8737668b"
    )
    original, target, baseline = [decode_artifact(load_artifact(p)) for p in paths[:3]]
    return original, target, actual, baseline, json.loads(paths[3].read_text())


@pytest.mark.capture
def test_genuine_copy_recapture_and_removal_reproduce_complete_observed_bodies(genuine_cell_copy):
    original, target, actual, baseline, registration = genuine_cell_copy
    checks, packets, changes, sound2_steps, keys = recapture_checks(
        original, target, actual, registration
    )
    assert all(checks.values())
    assert packets == [5, 7] and len(changes) == 4
    assert sound2_steps == [1, 9] and keys == {"1": 1, "5": 2, "9": 7, "13": 16}
    assert encode_packets(remove_sound_cell(actual, 1, 2, [9])) == original.encoded_body
    assert encode_packets(remove_sound_cell(original, 1, 2, [1])) == baseline.encoded_body
    assert encode_packets(remove_sound_cell(actual, 1, 2, [1, 9])) == baseline.encoded_body
    wrong_checks, _, _, _, _ = recapture_checks(original, target, original, registration)
    assert not wrong_checks["registered_body_hash_matches"]
    assert not wrong_checks["expected_sound2_steps"]


@pytest.mark.capture
@pytest.mark.parametrize("damage", ["sample", "neighbour"])
def test_recapture_rejects_valid_checksums_with_changed_other_state(genuine_cell_copy, damage):
    original, target, actual, _, registration = genuine_cell_copy
    packets = list(actual.packets)
    index, offset = (
        (4, 6)
        if damage == "neighbour"
        else (next(i for i, p in enumerate(packets) if p.tag == 0xEF78 and len(p.payload) > 9), 20)
    )
    data = bytearray(packets[index].payload)
    data[offset] ^= 1
    packets[index] = Packet(packets[index].tag, bytes(data))
    changed = decode_frame(encode_packets(packets), start=0)
    checks, _, _, sound2_steps, _ = recapture_checks(original, target, changed, registration)
    assert checks["all_packet_checksums_valid"] and sound2_steps == [1, 9]
    assert not checks["registered_body_hash_matches"]
    assert not checks[
        "sample_packets_unchanged" if damage == "sample" else "sound3_cells_unchanged"
    ]


@pytest.mark.capture
def test_removal_cli_preserves_source_and_rejects_aliases_and_empty_targets(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = root / "experiments/edited-sound2-cell-001/derived/analysis-001/capture.symbols.npz"
    if not source.exists():
        pytest.skip("Reviewed genuine two-cell recapture artifact required")
    before = source.read_bytes()
    output, report = tmp_path / "removed.npz", tmp_path / "remove.json"
    args = [
        "remove-sound-cell",
        str(source),
        "--pattern",
        "1",
        "--sound",
        "2",
        "--steps",
        "1",
        "--out",
        str(output),
        "--report",
        str(report),
    ]
    assert main(args) == 0
    result = json.loads(report.read_text())
    assert result["hardware_verified"] is False
    assert (
        result["native_frame"]["encoded_body_sha256"]
        == "1e493f1495ecf2dc68077a35ae97b8883acbe96b94d0798427a9f3f990a1761a"
    )
    assert main(args) == 2
    assert main(args[: args.index("--out")] + ["--out", str(source), "--force"]) == 2
    assert (
        main(
            [
                "remove-sound-cell",
                str(source),
                "--pattern",
                "1",
                "--sound",
                "2",
                "--steps",
                "5",
                "--out",
                str(tmp_path / "empty.npz"),
            ]
        )
        == 2
    )
    assert not (tmp_path / "empty.npz").exists()
    assert source.read_bytes() == before


@pytest.mark.capture
def test_genuine_removal_recapture_matches_target_and_preserves_neighbour_and_remaining_note():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-sound2-remove-001"
    paths = [
        root / "experiments/edited-sound2-cell-001/derived/analysis-001/capture.symbols.npz",
        root / "experiments/generated-sound2-remove-001/edited.symbols.npz",
        directory / "capture.wav",
        directory / "restore-registration.json",
    ]
    if not all(p.exists() for p in paths):
        pytest.skip("Genuine removal recapture, source, target and registration required")
    assert (
        sha256_file(paths[2]) == "aa8c083704bb92aa44893bafc3abd35e2bc05182fbb01ca7511f04752dafeb7d"
    )
    original, target = [decode_artifact(load_artifact(p)) for p in paths[:2]]
    actual = decode_artifact(decode_wav(paths[2], 0.0063))
    assert (
        hashlib.sha256(actual.encoded_body).hexdigest()
        == "1e493f1495ecf2dc68077a35ae97b8883acbe96b94d0798427a9f3f990a1761a"
    )
    registration = json.loads(paths[3].read_text())
    checks, packets, changes, steps, keys = removal_recapture_checks(
        original, target, actual, registration
    )
    assert all(checks.values()) and packets == [4, 7] and len(changes) == 4
    assert steps == [9] and keys == {"1": 1, "5": 2, "9": 7, "13": 16}
    wrong_checks, _, _, _, _ = removal_recapture_checks(original, target, original, registration)
    assert not wrong_checks["removed_sound2_cells_empty"]
    assert not wrong_checks["registered_body_hash_matches"]
    packets = list(actual.packets)
    data = bytearray(packets[4].payload)
    data[6:9] = bytes(3)  # Clearing Sound3 as well must never pass as Sound2-only removal.
    packets[4] = Packet(packets[4].tag, bytes(data))
    damaged = decode_frame(encode_packets(packets), start=0)
    wrong_checks, _, _, _, _ = removal_recapture_checks(original, target, damaged, registration)
    assert wrong_checks["all_packet_checksums_valid"] and wrong_checks["removed_sound2_cells_empty"]
    assert not wrong_checks["sound3_cells_unchanged"]
    assert not wrong_checks["target_body_matches"]
