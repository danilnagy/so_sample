"""Compare the first generated drum-cell copy recapture with its exact saved target."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact


def comparison_checks(original, target, actual, registration):
    before, after = pattern_data(original, 1), pattern_data(actual, 1)
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packets = [i for i, (a, b) in enumerate(zip(original.packets, actual.packets)) if a != b]
    drum_steps = [
        step
        for step in range(1, 17)
        if any(after[48 * (step - 1) + 27 : 48 * (step - 1) + 30])
        or after[768 + 16 * (step - 1) + 9]
    ]
    checks = {
        "registered_body_hash_matches": hashlib.sha256(actual.encoded_body).hexdigest()
        == registration["expected_encoded_body_sha256"],
        "target_body_matches": actual.encoded_body == target.encoded_body,
        "target_plain_packets_match": actual.packets == target.packets,
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
        "packet_count": len(original.packets)
        == len(target.packets)
        == len(actual.packets)
        == registration["expected_packet_count"],
        "frame_end_byte": actual.end_byte == registration["expected_frame_end_byte"],
        "only_expected_plain_packets_changed": packets
        == registration["expected_changed_plain_packet_indices"],
        "only_expected_pattern_bytes_changed": changes
        == registration["expected_pattern_byte_changes"],
        "sample_and_reference_packets_unchanged": tuple(
            p for p in original.packets if p.tag in (0x68B5, 0xEF78)
        )
        == tuple(p for p in actual.packets if p.tag in (0x68B5, 0xEF78)),
        "other15_patterns_unchanged": all(
            pattern_data(original, p) == pattern_data(actual, p) for p in range(2, 17)
        ),
        "all_melodic_sound2_and_sound3_cells_preserved": all(
            before[48 * s + 3 : 48 * s + 9] == after[48 * s + 3 : 48 * s + 9]
            and before[768 + 16 * s + 1 : 768 + 16 * s + 3]
            == after[768 + 16 * s + 1 : 768 + 16 * s + 3]
            for s in range(16)
        ),
        "source_drum_step1_preserved": before[27:30] == after[27:30] and before[777] == after[777],
        "expected_drum_steps": drum_steps == registration["expected_sound10_steps"],
        "observed_raw_drum_pair_preserved": all(
            after[48 * (step - 1) + 27 : 48 * (step - 1) + 30].hex()
            == registration["expected_drum_primary_hex"]
            and after[768 + 16 * (step - 1) + 9] == registration["expected_drum_auxiliary_byte"]
            for step in drum_steps
        ),
        "footer_unchanged": before[1024:] == after[1024:],
    }
    return checks, packets, changes, drum_steps


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-drum-cell-copy-001"
    registration_path = directory / "restore-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path, target_path, restore_path = [
        directory / registration[key]
        for key in ("source_artifact", "generated_artifact", "restore_wav")
    ]
    capture, actual_path = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    output = directory / "hardware-validation.json"
    validate_outputs(
        [output],
        [registration_path, source_path, target_path, restore_path, capture, actual_path],
        False,
    )
    artifacts = [load_artifact(p) for p in (source_path, target_path, actual_path)]
    original, target, actual = [decode_artifact(a) for a in artifacts]
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or artifacts[0].metadata["source_sha256"] != registration["source_backup_sha256"]
        or hashlib.sha256(original.encoded_body).hexdigest() != registration["source_body_sha256"]
        or sha256_file(target_path) != registration["generated_artifact_sha256"]
        or sha256_file(restore_path) != registration["restore_wav_sha256"]
        or artifacts[2].metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Source, generated target, restore or recapture differs from registration")
    checks, packets, changes, drum_steps = comparison_checks(original, target, actual, registration)
    report = {
        "analysis_version": "first-drum-cell-copy-hardware-validation-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(actual_path),
        "decoder_version": artifacts[2].metadata["decoder_version"],
        "checks": checks,
        "passed": all(checks.values()),
        "hardware_verified": all(checks.values()),
        "changed_plain_packet_indices": packets,
        "pattern1_byte_changes": changes,
        "sound10_steps": drum_steps,
        "native_frame": frame_report(actual),
        "manual_observation_status": "Grid/playback observations must be recorded separately; this report verifies native state",
        "limits": registration["limits"],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Drum-cell recapture differs from target; report retained")


if __name__ == "__main__":
    main()
