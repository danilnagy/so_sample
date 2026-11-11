"""Validate the first generated Sound9/key1 edit against its registered hardware target."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report, sound_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sample_start_control import reference_comparison_checks


def comparison_checks(original, target, actual, registration):
    if (
        registration["expected_sound_slot"],
        registration["expected_slice_key"],
        registration["expected_selector_id"],
    ) != (9, 1, 8):
        raise ValueError("This hardware validator supports only the registered Sound9/key1 test")
    local_registration = {
        "expected_change": {"sound_slot": 9},
        "control_checks": {
            "packet_count": registration["expected_packet_count"],
            "frame_end_byte": registration["expected_frame_end_byte"],
            "sound3_reference_packet_index": 383,
            "sound3_reference_before_hex": registration["source_reference_hex"],
            "sound3_record_size": 9,
            "sound3_owner_id": registration["expected_owner_id"],
            "only_allowed_payload_offsets": [4, 5, 6, 7],
        },
    }
    checks, packets, changes, values = reference_comparison_checks(
        original, actual, local_registration
    )
    checks.update(
        registered_body_hash_matches=hashlib.sha256(actual.encoded_body).hexdigest()
        == registration["expected_encoded_body_sha256"],
        target_body_matches=actual.encoded_body == target.encoded_body,
        target_plain_packets_match=actual.packets == target.packets,
        expected_reference_hex=sound_data(actual, 8).hex()
        == registration["expected_reference_hex"],
        expected_changed_packets=packets == registration["expected_changed_plain_packet_indices"],
        expected_reference_byte_changes=changes == registration["expected_reference_byte_changes"],
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
    directory = root / "experiments/edited-drum9-slice-end-001"
    registration_path = directory / "restore-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path, target_path, restore_path = [
        directory / registration[key]
        for key in ("source_artifact", "generated_artifact", "restore_wav")
    ]
    capture = directory / "capture.wav"
    actual_path = directory / "derived/analysis-001/capture.symbols.npz"
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
        or sha256_file(restore_path) != registration["restore_wav_sha256"]
        or artifacts[2].metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Source, restore file or recapture identity differs from registration")
    checks, packets, changes, values = comparison_checks(original, target, actual, registration)
    report = {
        "analysis_version": "first-drum-slice-hardware-validation-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(actual_path),
        "decoder_version": artifacts[2].metadata["decoder_version"],
        "checks": checks,
        "passed": all(checks.values()),
        "hardware_verified": all(checks.values()),
        "native_frame": frame_report(actual),
        "changed_plain_packet_indices": packets,
        "reference_byte_changes": changes,
        "reference_values": values,
        "user_report": "done and pass",
        "manual_observations": "User confirms restore, clear short Sound9/key1 tone and unchanged longer Sound8/key1 tone; no deviation reported",
        "capture_timing": "Requested before audition or pattern playback; user reports completion without deviation",
        "limits": [
            "Only this local Sound9/key1 zero-start endpoint edit is independently hardware accepted",
            "Audible checks are user reported; exact device duration, pitch and endpoint inclusivity remain unmeasured",
            "Other keys, starts, drum slots and general minimum rules remain unverified; the original79 prediction stays failed",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Drum-slice recapture differs from the target; report retained")


if __name__ == "__main__":
    main()
