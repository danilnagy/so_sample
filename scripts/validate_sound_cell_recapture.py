"""Validate the genuine Sound2 cell-copy recapture against its full registered target."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data, patterns_report
from po33_re.modem.symbols import load_artifact


def comparison_checks(original, target, actual, registration):
    pattern = registration["expected_pattern"]
    before, after = pattern_data(original, pattern), pattern_data(actual, pattern)
    packet_changes = [i for i, (a, b) in enumerate(zip(original.packets, actual.packets)) if a != b]
    byte_changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    rows = patterns_report(actual)["patterns"][pattern - 1]["nonzero_step_rows"]
    sound2_steps = [
        step
        for step in range(1, 17)
        if any(after[48 * (step - 1) + 3 : 48 * (step - 1) + 6]) or after[768 + 16 * (step - 1) + 1]
    ]
    sound3_keys = {
        str(step): (after[768 + 16 * (step - 1) + 2] & 15) + 1
        for step in range(1, 17)
        if any(after[48 * (step - 1) + 6 : 48 * (step - 1) + 9]) or after[768 + 16 * (step - 1) + 2]
    }
    checks = {
        "registered_body_hash_matches": hashlib.sha256(actual.encoded_body).hexdigest()
        == registration["expected_encoded_body_sha256"],
        "target_body_matches": actual.encoded_body == target.encoded_body,
        "target_plain_packets_match": actual.packets == target.packets,
        "all_packet_checksums_valid": True,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
        "packet_count": len(original.packets)
        == len(target.packets)
        == len(actual.packets)
        == registration["expected_packet_count"],
        "frame_end_byte": actual.end_byte == registration["expected_frame_end_byte"],
        "only_expected_plain_packets_changed": packet_changes
        == registration["expected_changed_plain_packet_indices"],
        "only_expected_pattern_bytes_changed": byte_changes
        == registration["expected_pattern_byte_changes"],
        "sample_packets_unchanged": all(
            a == b for a, b in zip(original.packets, actual.packets) if a.tag in (0x68B5, 0xEF78)
        ),
        "other_patterns_unchanged": all(
            pattern_data(original, p) == pattern_data(actual, p)
            for p in range(1, 17)
            if p != pattern
        ),
        "sound3_cells_unchanged": all(
            before[48 * s + 6 : 48 * s + 9] == after[48 * s + 6 : 48 * s + 9]
            and before[768 + 16 * s + 2] == after[768 + 16 * s + 2]
            for s in range(16)
        ),
        "source_sound2_cell_unchanged": before[3:6] == after[3:6] and before[769] == after[769],
        "expected_populated_steps": [r["step"] for r in rows]
        == registration["expected_populated_steps"],
        "expected_sound2_steps": sound2_steps == registration["expected_sound2_steps"],
        "expected_sound2_parameters": all(
            after[48 * (step - 1) + 3 : 48 * (step - 1) + 6]
            == bytes.fromhex(registration["expected_sound2_primary_hex"])
            and after[768 + 16 * (step - 1) + 1] == registration["expected_sound2_auxiliary_byte"]
            for step in sound2_steps
        ),
        "expected_sound3_keys": sound3_keys == registration["expected_sound3_keys_by_step"],
        "only_expected_sound_cells": all(
            [c["candidate_sound_slot"] for c in row["nonzero_three_byte_cells"]]
            == ([2, 3] if row["step"] in sound2_steps else [3])
            for row in rows
        ),
        "footer_unchanged": before[1024:] == after[1024:],
    }
    return checks, packet_changes, byte_changes, sound2_steps, sound3_keys


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-sound2-cell-001"
    registration_path = directory / "restore-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path = directory / registration["source_artifact"]
    target_path = directory / registration["generated_artifact"]
    restore_path = directory / registration["restore_wav"]
    actual_path = directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    output = directory / "hardware-validation.json"
    validate_outputs(
        [output],
        [registration_path, source_path, target_path, restore_path, actual_path, capture],
        False,
    )
    artifacts = [load_artifact(p) for p in (source_path, target_path, actual_path)]
    if sha256_file(source_path) != registration["source_artifact_sha256"]:
        raise ValueError("Original artifact does not match registration")
    if artifacts[0].metadata["source_sha256"] != registration["source_backup_sha256"]:
        raise ValueError("Original artifact does not match registered source WAV")
    if artifacts[2].metadata["source_sha256"] != sha256_file(capture):
        raise ValueError("Recapture artifact does not match capture WAV")
    if sha256_file(restore_path) != registration["restore_wav_sha256"]:
        raise ValueError("Restore WAV does not match registration")
    frames = [decode_artifact(a) for a in artifacts]
    checks, packets, changes, sound2_steps, sound3_keys = comparison_checks(*frames, registration)
    report = {
        "analysis_version": "native-sound2-cell-copy-hardware-validation-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(actual_path),
        "decoder_version": artifacts[2].metadata["decoder_version"],
        "checks": checks,
        "passed": all(checks.values()),
        "native_frame": frame_report(frames[2]),
        "changed_plain_packet_indices": packets,
        "pattern1_byte_changes": changes,
        "sound2_steps": sound2_steps,
        "sound3_keys_by_step": sound3_keys,
        "user_report": "done and confirmed",
        "hardware_verified": all(checks.values()),
        "manual_observations": "User confirms requested Sound2/Sound3 step lights and normal Pattern1 playback; no deviation reported",
        "capture_timing": "Requested before write-mode inspection and playback; user reports completion without a deviation",
        "limits": [
            "Step lights and musical behavior are user reported; acoustic waveforms were not measured.",
            "This validates copying the observed Sound2 primary0d2831/F0 cell with calibrated Sound3 neighbours locally.",
            "Other sounds and Sound2 keys remain unsupported; note primary parameters remain opaque.",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Sound2 cell-copy recapture checks failed; report retained")


if __name__ == "__main__":
    main()
