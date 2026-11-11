"""Validate the registered nonzero-start drum edit using the separately saved retry."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report, sound_data, sound_groups
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_slice_control import reference_comparison_checks


def comparison_checks(original, target, actual, registration):
    if (
        registration["expected_sound_slot"],
        registration["expected_slice_key"],
        registration["expected_selector_id"],
    ) != (9, 2, 9):
        raise ValueError("Only the registered Sound9/key2 test is supported")
    groups = sound_groups(original)
    local = {
        "control_checks": {
            "packet_count": registration["expected_packet_count"],
            "frame_end_byte": registration["expected_frame_end_byte"],
            "sound9_selector_ids": list(range(8, 24)),
            "reference_packet_indices": {str(key): groups[key] for key in range(8, 24)},
            "reference_before_hex": {
                str(key): sound_data(original, key).hex() for key in range(8, 24)
            },
            "reference_record_bytes": 9,
            "owner_id": registration["expected_owner_id"],
            "only_allowed_payload_offsets": [4, 5, 6, 7],
        }
    }
    checks, packets, selectors, changes, values = reference_comparison_checks(
        original, actual, local
    )
    checks.update(
        registered_source_reference=sound_data(original, 9).hex()
        == registration["source_reference_hex"],
        registered_body_hash_matches=hashlib.sha256(actual.encoded_body).hexdigest()
        == registration["expected_encoded_body_sha256"],
        target_body_matches=actual.encoded_body == target.encoded_body,
        target_plain_packets_match=actual.packets == target.packets,
        expected_reference_hex=sound_data(actual, 9).hex()
        == registration["expected_reference_hex"],
        expected_changed_packets=packets == registration["expected_changed_plain_packet_indices"],
        expected_changed_selector=selectors == [registration["expected_selector_id"]],
        expected_reference_byte_changes=changes == registration["expected_reference_byte_changes"],
        start_field_unchanged=values is not None
        and values["before"]["first_u32le"]
        == values["after"]["first_u32le"]
        == registration["expected_start_field"],
        endpoint_field_matches=values is not None
        and values["after"]["second_u32le"] == registration["expected_endpoint_field"],
        accepted_key1_preserved=sound_data(original, 8)
        == sound_data(actual, 8)
        == bytes.fromhex(registration["expected_preserved_key1_reference_hex"]),
        target_packet_count=len(target.packets) == registration["expected_packet_count"],
    )
    return checks, packets, selectors, changes, values


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-drum9-key2-end-001"
    registration_path, retry_path = (
        directory / "restore-registration.json",
        directory / "recapture-retry-registration.json",
    )
    registration, retry = [json.loads(p.read_text()) for p in (registration_path, retry_path)]
    source_path, target_path, restore_path = [
        directory / registration[key]
        for key in ("source_artifact", "generated_artifact", "restore_wav")
    ]
    capture = directory / retry["expected_file"]
    actual_path = directory / "derived/analysis-003/capture.symbols.npz"
    output = directory / "hardware-validation.json"
    validate_outputs(
        [output],
        [
            registration_path,
            retry_path,
            source_path,
            target_path,
            restore_path,
            capture,
            actual_path,
        ],
        False,
    )
    artifacts = [load_artifact(p) for p in (source_path, target_path, actual_path)]
    original, target, actual = [decode_artifact(a) for a in artifacts]
    if (
        sha256_file(registration_path) != retry["restore_target_registration_sha256"]
        or sha256_file(source_path) != registration["source_artifact_sha256"]
        or artifacts[0].metadata["source_sha256"] != registration["source_backup_sha256"]
        or hashlib.sha256(original.encoded_body).hexdigest() != registration["source_body_sha256"]
        or sha256_file(restore_path) != registration["restore_wav_sha256"]
        or artifacts[2].metadata["source_sha256"] != sha256_file(capture)
        or retry["expected_encoded_body_sha256"] != registration["expected_encoded_body_sha256"]
    ):
        raise ValueError("Source, restore target or retry identity differs from registration")
    checks, packets, selectors, changes, values = comparison_checks(
        original, target, actual, registration
    )
    archive = directory / retry["prior_failed_capture_archive"]
    report = {
        "analysis_version": "nonzero-start-drum-key2-hardware-validation-0.1",
        "registration_sha256": sha256_file(registration_path),
        "retry_registration_sha256": sha256_file(retry_path),
        "capture_file": "capture-retry.wav",
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(actual_path),
        "decoder_version": artifacts[2].metadata["decoder_version"],
        "checks": checks,
        "passed": all(checks.values()),
        "hardware_verified": all(checks.values()),
        "changed_plain_packet_indices": packets,
        "changed_selector_ids": selectors,
        "reference_byte_changes": changes,
        "reference_values": values,
        "native_frame": frame_report(actual),
        "restore_and_tone_check_user_report": "done and confirmed",
        "retry_user_report": "updated the recording",
        "manual_observations": "User confirms restore and both short Sound9/key2 and preserved key1 tones; retry recorded afterward without reported state changes",
        "provenance": {
            "retry_uploaded_as": "capture.wav",
            "retry_preserved_as": "capture-retry.wav",
            "failed_first_capture_archive": "capture-attempt-001.wav",
            "failed_first_capture_archive_hash_matches": archive.exists()
            and sha256_file(archive) == retry["prior_failed_capture_sha256"],
            "failed_artifacts_and_reports_retained": True,
        },
        "limits": [
            "This registered fixed-start key2 endpoint6045 edit is accepted; arbitrary starts, other drum keys and all possible combinations are not established",
            "Both tone checks are user reported; exact rendering duration, pitch/gain and endpoint inclusivity remain unmeasured",
            "General minimum and autoslice rules remain unresolved; previous failed predictions and recapture attempt are retained",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Key2 recapture differs from target; report retained")


if __name__ == "__main__":
    main()
