"""Validate the clean Sound10-copy retry against its independently saved predictions."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report, sound_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import reference_comparison_checks


def comparison_checks(base, frame, registration):
    checks, changed, records, populated = reference_comparison_checks(base, frame, registration)
    ids = registration["control_checks"]["candidate_destination_selector_ids"]
    hypotheses = registration["separately_evaluated_hypotheses"]
    reference = hypotheses["destination_records_are_owner0_references"]
    expected_records = hypotheses["destination_records_equal_original_sound9_autocopy"][
        "expected_payload_hex_by_destination_id"
    ]
    packet_delta = len(frame.packets) - len(base.packets)
    byte_delta = len(frame.encoded_body) - len(base.encoded_body)
    fits = {
        "sound10_uses_selector_block24_to39": bool(changed)
        and set(changed) <= set(ids)
        and checks["every_other_plain_packet_unchanged"],
        "all16_destination_groups_populated": populated
        == hypotheses["all16_destination_groups_populated"]["populated_ids"],
        "destination_records_are_owner0_references": bool(records)
        and all(
            r["bytes"] == reference["record_bytes"] and r.get("owner_id") == reference["owner_id"]
            for r in records
        ),
        "destination_records_equal_original_sound9_autocopy": set(populated) == set(ids)
        and all(r["payload_hex"] == expected_records[str(r["selector_id"])] for r in records),
        "sixteen_new_reference_packets_only": packet_delta
        == hypotheses["sixteen_new_reference_packets_only"]["packet_count_delta"]
        and byte_delta
        == hypotheses["sixteen_new_reference_packets_only"]["native_body_byte_delta"],
    }
    return checks, fits, changed, records


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-018-b-copy-sound1-to-drum10"
    registration_path = root / "experiments/drum10-copy-predictions-001.json"
    retry_path = directory / "recapture-retry-registration.json"
    registration, retry = [json.loads(p.read_text()) for p in (registration_path, retry_path)]
    source_path = directory / registration["baseline_artifact"]
    capture = directory / retry["expected_file"]
    artifact_path = directory / "derived/analysis-004/capture.symbols.npz"
    original_copy = registration["separately_evaluated_hypotheses"][
        "destination_records_equal_original_sound9_autocopy"
    ]
    original_copy_path = directory / original_copy["reference_source_artifact"]
    output = root / "experiments/drum10-copy-results-001.json"
    validate_outputs(
        [output],
        [registration_path, retry_path, source_path, capture, artifact_path, original_copy_path],
        False,
    )
    source, recorded = load_artifact(source_path), load_artifact(artifact_path)
    base, frame = decode_artifact(source), decode_artifact(recorded)
    prior = decode_artifact(load_artifact(original_copy_path))
    if (
        sha256_file(registration_path) != retry["original_preregistration_sha256"]
        or sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
        or sha256_file(original_copy_path) != original_copy["reference_source_artifact_sha256"]
        or any(
            sound_data(prior, 8 + i).hex()
            != original_copy["expected_payload_hex_by_destination_id"][str(24 + i)]
            for i in range(16)
        )
    ):
        raise ValueError("Source, retry or original-copy reference differs from registration")
    checks, fits, changed, records = comparison_checks(base, frame, registration)
    archive = directory / retry["prior_failed_capture_archive"]
    report = {
        "analysis_version": "second-drum-block-copy-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "retry_registration_sha256": sha256_file(retry_path),
        "capture_file": "capture-retry.wav",
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "changed_selector_ids": changed,
        "destination_records": records,
        "packet_count_delta": len(frame.packets) - len(base.packets),
        "native_body_byte_delta": len(frame.encoded_body) - len(base.encoded_body),
        "native_frame": frame_report(frame),
        "initial_user_report": "done",
        "retry_user_report": "updated the file",
        "failed_first_capture_preserved": archive.exists()
        and sha256_file(archive) == retry["prior_failed_capture_sha256"],
        "sound10_writer_enabled": False,
        "sound10_preview_enabled": False,
        "limits": [
            "Sound10's selector24..39 block is independently observed; individual keyboard-key mapping still needs a direct control",
            "The exact fresh-copy reference prediction uses the original Sound9 copy before trims; no general autoslice formula is inferred",
            "No new owned buffer is observed in this copy; other allocation behaviors and drum slots remain unverified",
            "The failed first waveform and all diagnostic attempts remain archived; only the clean retry evaluates these hypotheses",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Sound10-copy preservation failed; report retained")


if __name__ == "__main__":
    main()
