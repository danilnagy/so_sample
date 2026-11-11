"""Compare the genuine fixed-start endpoint recapture against its full target."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_sample_start_control import reference_comparison_checks


def comparison_checks(original, target, actual, registration):
    reference_registration = {
        "expected_change": {"sound_slot": 3},
        "control_checks": {
            "packet_count": registration["expected_packet_count"],
            "frame_end_byte": registration["expected_frame_end_byte"],
            "sound3_reference_packet_index": 375,
            "sound3_reference_before_hex": registration.get(
                "source_sound3_header_hex", "a17a0000107b000000"
            ),
            "sound3_record_size": 9,
            "sound3_owner_id": 0,
            "only_allowed_payload_offsets": [4, 5, 6, 7],
        },
    }
    checks, packets, changes, values = reference_comparison_checks(
        original, actual, reference_registration
    )
    checks.update(
        registered_body_hash_matches=hashlib.sha256(actual.encoded_body).hexdigest()
        == registration["expected_encoded_body_sha256"],
        target_body_matches=actual.encoded_body == target.encoded_body,
        target_plain_packets_match=actual.packets == target.packets,
        expected_changed_packets=packets == registration["expected_changed_plain_packet_indices"],
        expected_reference_byte_changes=changes
        == registration["expected_sound3_reference_byte_changes"],
        start_field_unchanged=values["before"]["first_u32le"]
        == values["after"]["first_u32le"]
        == registration["expected_start_field"],
        endpoint_field_matches=values["after"]["second_u32le"]
        == registration["expected_endpoint_field"],
        target_packet_count=len(target.packets) == registration["expected_packet_count"],
    )
    return checks, packets, changes, values


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-nonzero-trim-001"
    registration_path = directory / "restore-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path, target_path, restore_path = [
        directory / registration[k]
        for k in ("source_artifact", "generated_artifact", "restore_wav")
    ]
    capture = directory / "capture.wav"
    actual_path = directory / "derived/analysis-001/capture.symbols.npz"
    output = directory / "hardware-validation.json"
    validate_outputs(
        [output],
        [registration_path, source_path, target_path, restore_path, actual_path, capture],
        False,
    )
    artifacts = [load_artifact(p) for p in (source_path, target_path, actual_path)]
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or artifacts[0].metadata["source_sha256"] != registration["source_backup_sha256"]
    ):
        raise ValueError("Source artifact identity differs from registration")
    if artifacts[2].metadata["source_sha256"] != sha256_file(capture):
        raise ValueError("Recapture artifact does not match capture WAV")
    if sha256_file(restore_path) != registration["restore_wav_sha256"]:
        raise ValueError("Restore WAV differs from registration")
    original, target, actual = [decode_artifact(a) for a in artifacts]
    checks, packets, changes, values = comparison_checks(original, target, actual, registration)
    report = {
        "analysis_version": "fixed-start-endpoint-hardware-validation-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(actual_path),
        "decoder_version": artifacts[2].metadata["decoder_version"],
        "checks": checks,
        "passed": all(checks.values()),
        "native_frame": frame_report(actual),
        "changed_plain_packet_indices": packets,
        "sound3_reference_byte_changes": changes,
        "sound3_header_values": values,
        "user_report": "done, and both checks passed",
        "hardware_verified": all(checks.values()),
        "manual_observations": "User confirms clearly audible brief Sound3 key1 tone and unchanged longer Sound8 key1 tone; no deviation reported",
        "capture_timing": "Requested before audition; user reports protocol completion without a deviation",
        "limits": [
            "Tone checks are user reported; exact duration and frequencies were not independently measured",
            "Only the local fixed-start Sound3 endpoint edit is hardware validated; other starts and general minimum rules remain unresolved",
            "Sample previews retain an explicit half-open convention; exact hardware endpoint inclusivity is unresolved",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Fixed-start endpoint recapture differs; report retained")


if __name__ == "__main__":
    main()
