"""Validate the first generated cross-drum copy against its preregistered target."""

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
    ) != (10, 1, 24):
        raise ValueError("Only the registered Sound10/key1 cross-drum test is supported")
    ids = list(range(24, 40))
    groups = sound_groups(original)
    local = {
        "control_checks": {
            "packet_count": registration["expected_packet_count"],
            "frame_end_byte": registration["expected_frame_end_byte"],
            "sound9_selector_ids": ids,
            "reference_packet_indices": {str(key): groups[key] for key in ids},
            "reference_before_hex": {str(key): sound_data(original, key).hex() for key in ids},
            "reference_record_bytes": 9,
            "owner_id": registration["expected_owner_id"],
            "only_allowed_payload_offsets": list(range(8)),
        }
    }
    checks, packets, selectors, changes, values = reference_comparison_checks(
        original, actual, local
    )
    checks["exactly_one_sound10_reference_changed"] = checks.pop(
        "exactly_one_sound9_reference_changed"
    )
    checks.update(
        registered_source_reference=sound_data(original, 24).hex()
        == registration["source_reference_hex"],
        registered_body_hash_matches=hashlib.sha256(actual.encoded_body).hexdigest()
        == registration["expected_encoded_body_sha256"],
        target_body_matches=actual.encoded_body == target.encoded_body,
        target_plain_packets_match=actual.packets == target.packets,
        exact_source_key2_reference_copied=sound_data(actual, 24)
        == sound_data(original, 9)
        == bytes.fromhex(registration["expected_reference_hex"]),
        expected_changed_packets=packets == registration["expected_changed_plain_packet_indices"],
        expected_changed_selector=selectors == [24],
        expected_reference_byte_changes=changes == registration["expected_reference_byte_changes"],
        target_packet_count=len(target.packets) == registration["expected_packet_count"],
    )
    return checks, packets, selectors, changes, values


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-drum-slice-copy-001"
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
        or sha256_file(target_path) != registration["generated_artifact_sha256"]
        or sha256_file(restore_path) != registration["restore_wav_sha256"]
        or artifacts[2].metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Source, generated target, restore or recapture differs from registration")
    checks, packets, selectors, changes, values = comparison_checks(
        original, target, actual, registration
    )
    report = {
        "analysis_version": "cross-drum-slice-copy-hardware-validation-0.1",
        "registration_sha256": sha256_file(registration_path),
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
        "audition_status": "User observations must be recorded separately; this report verifies native state",
        "limits": [
            "Acceptance applies to this exact existing-reference copy, not arbitrary drum slots/keys or allocation",
            "Tone/filter rendering, endpoint inclusivity and destination endpoint editing remain unresolved",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Cross-drum recapture differs from target; report retained")


if __name__ == "__main__":
    main()
