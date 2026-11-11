"""Validate the registered retry independently of the replaced, failed source WAV."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.validate_nonzero_trim_recapture import comparison_checks


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-quarter-window-001"
    registration_path = directory / "restore-registration.json"
    retry_path = directory / "recapture-retry-registration.json"
    registration, retry = [json.loads(p.read_text()) for p in (registration_path, retry_path)]
    capture = directory / retry["expected_file"]
    source_path, target_path, restore_path = [
        directory / registration[key]
        for key in ("source_artifact", "generated_artifact", "restore_wav")
    ]
    actual_path = directory / "derived/analysis-003/capture.symbols.npz"
    output = directory / "hardware-validation.json"
    validate_outputs(
        [output],
        [
            registration_path,
            retry_path,
            capture,
            source_path,
            target_path,
            restore_path,
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
    checks, packets, changes, values = comparison_checks(original, target, actual, registration)
    report = {
        "analysis_version": "second-start-window-hardware-validation-0.1",
        "registration_sha256": sha256_file(registration_path),
        "retry_registration_sha256": sha256_file(retry_path),
        "capture_file": "capture-retry.wav",
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(actual_path),
        "decoder_version": artifacts[2].metadata["decoder_version"],
        "checks": checks,
        "passed": all(checks.values()),
        "hardware_verified": all(checks.values()),
        "native_frame": frame_report(actual),
        "changed_plain_packet_indices": packets,
        "sound3_reference_byte_changes": changes,
        "sound3_header_values": values,
        "restore_and_tone_check_user_report": "done and passed",
        "retry_user_report": "done",
        "manual_observations": "User confirms restore and both requested tone checks; retry recorded afterward without reported state changes",
        "provenance": {
            "retry_uploaded_as": "capture.wav",
            "retry_preserved_as": "capture-retry.wav",
            "first_failed_wav_sha256": retry["prior_failed_capture_sha256"],
            "first_failed_wav_still_available": False,
            "first_failed_artifact_and_reports_retained": True,
            "note": "The user replaced capture.wav with the retry; the old WAV cannot be recovered from its hash or artifact",
        },
        "limits": [
            "Only this registered second-start endpoint window has matching hardware evidence",
            "Tone duration and frequencies are user reported rather than independently measured",
            "General minimum-width rules, interpolated start values and endpoint inclusivity remain unresolved",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Second-start recapture differs; report retained")


if __name__ == "__main__":
    main()
