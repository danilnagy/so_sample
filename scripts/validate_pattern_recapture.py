"""Validate the registered four-note restore once its recapture is available."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data, pattern_groups, patterns_report
from po33_re.modem.symbols import load_artifact


def comparison_checks(original, target, actual, registration):
    pattern_slot = registration["expected_pattern"]
    rows = patterns_report(actual)["patterns"][pattern_slot - 1]["nonzero_step_rows"]
    actual_steps = [row["step"] for row in rows]
    changes = [i for i, (a, b) in enumerate(zip(original.packets, actual.packets)) if a != b]
    allowed = set(pattern_groups(original)[pattern_slot - 1])
    source_data, actual_data = (
        pattern_data(original, pattern_slot),
        pattern_data(actual, pattern_slot),
    )
    source_primary, source_auxiliary = source_data[:48], source_data[768:784]
    body_hash = hashlib.sha256(actual.encoded_body).hexdigest()
    checks = {
        "registered_body_sha256_matches": body_hash == registration["expected_encoded_body_sha256"],
        "generated_body_matches_recapture": target.encoded_body == actual.encoded_body,
        "generated_plain_packets_match_recapture": target.packets == actual.packets,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
        "all_packet_checksums_valid": True,
        "packet_count_unchanged": len(original.packets)
        == len(target.packets)
        == len(actual.packets)
        == registration["expected_packet_count"],
        "expected_frame_end_byte": actual.end_byte == registration["expected_frame_end_byte"],
        "only_pattern_data_packets_changed": bool(changes) and set(changes) <= allowed,
        "sample_packets_unchanged": all(
            a == b for a, b in zip(original.packets, actual.packets) if a.tag in (0x68B5, 0xEF78)
        ),
        "packet_tags_and_lengths_unchanged": all(
            a.tag == b.tag and len(a.payload) == len(b.payload)
            for a, b in zip(original.packets, actual.packets)
        ),
        "other_patterns_unchanged": all(
            pattern_data(original, slot) == pattern_data(actual, slot)
            for slot in range(1, 17)
            if slot != pattern_slot
        ),
        "expected_populated_steps": actual_steps == registration["expected_populated_steps"],
        "all_populated_raw_rows_match_source": all(
            actual_data[48 * (step - 1) : 48 * step] == source_primary
            and actual_data[768 + 16 * (step - 1) : 768 + 16 * step] == source_auxiliary
            for step in actual_steps
        ),
        "opaque_footer_unchanged": source_data[1024:] == actual_data[1024:],
    }
    return checks, changes, actual_steps


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-pattern-001"
    registration_path = directory / "experiment.json"
    registration = json.loads(registration_path.read_text())
    original_path = (
        root / "experiments/event-007-b-melodic/derived/analysis-001/capture.symbols.npz"
    )
    target_path = root / "experiments/generated-pattern-four-001/edited.symbols.npz"
    actual_path = directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    if not capture.is_file() or not actual_path.is_file():
        raise ValueError(
            "Recorded capture.wav and its reviewed decoded artifact are required; no hardware validation report created"
        )
    output = directory / "hardware-validation.json"
    validate_outputs(
        [output], [registration_path, original_path, target_path, actual_path, capture], False
    )
    artifacts = [load_artifact(p) for p in (original_path, target_path, actual_path)]
    if artifacts[0].metadata["source_sha256"] != registration["source_backup_sha256"]:
        raise ValueError("Original artifact does not match the registered source backup")
    source_hash = sha256_file(capture)
    if artifacts[2].metadata["source_sha256"] != source_hash:
        raise ValueError("Recapture artifact does not match its WAV")
    frames = [decode_artifact(a) for a in artifacts]
    checks, changes, steps = comparison_checks(*frames, registration)
    observation = json.loads((directory / "hardware-observation.json").read_text())
    context_path = directory / "capture-context.json"
    context = (
        json.loads(context_path.read_text())
        if context_path.is_file()
        else {"relative_to_pattern_playback": "not_reported"}
    )
    report = {
        "analysis_version": "native-pattern-hardware-validation-0.1",
        "capture_sha256": source_hash,
        "recapture_artifact_sha256": sha256_file(actual_path),
        "generated_artifact_sha256": sha256_file(target_path),
        "checks": checks,
        "passed": all(checks.values()),
        "changed_plain_packet_indices": changes,
        "populated_steps": steps,
        "native_frame": frame_report(frames[2]),
        "user_report": observation["user_report"],
        "capture_context": context,
        "restore_and_playback_reported_success": observation[
            "restore_and_playback_reported_success"
        ],
        "hardware_verified": all(checks.values())
        and observation["restore_and_playback_reported_success"],
        "limits": [
            "Restore and four-note playback are user reported; no independent playback audio is supplied.",
            "The checksum-validated native body is compared; acquisition and post-frame carrier are separate.",
            "This verifies this opaque-step copy on this local device path, not general note bitfield edits.",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Registered pattern recapture checks failed; mismatch report preserved")


if __name__ == "__main__":
    main()
