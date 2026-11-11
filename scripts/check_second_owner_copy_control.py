"""Compare a physical Sound4-to5 copy with reference versus buffer-copy predictions."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report, sound_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import reference_comparison_checks


def comparison_checks(base, frame, registration):
    checks, changed, records, populated = reference_comparison_checks(base, frame, registration)
    expected = registration["control_checks"]
    source = sound_data(base, expected["source_selector_id"])
    checks.update(
        baseline_second_owner_payload=hashlib.sha256(source).hexdigest()
        == expected["source_payload_sha256"],
        baseline_second_owner_header=source[:9].hex() == expected["source_header_hex"],
        baseline_second_owner_code_count=len(source) - 9 == expected["source_code_count"],
        destination_populated=populated == [4],
    )
    destination = b""
    if populated == [4]:
        destination = sound_data(frame, 4)
    hypotheses = registration["separately_evaluated_hypotheses"]
    reference = hypotheses["destination_is_exact_owner3_reference"]
    duplicate = hypotheses["destination_is_duplicate_self_owned_buffer"]
    geometry = hypotheses["one_new_reference_packet_only"]
    fits = {
        "destination_is_exact_owner3_reference": destination.hex()
        == reference["expected_payload_hex"],
        "destination_is_duplicate_self_owned_buffer": len(destination)
        == 9 + duplicate["expected_buffer_code_count"]
        and destination[:8] == source[:8]
        and destination[8] == duplicate["owner_id"]
        and destination[9:] == source[9:],
        "one_new_reference_packet_only": len(frame.packets) - len(base.packets)
        == geometry["packet_count_delta"]
        and len(frame.encoded_body) - len(base.encoded_body) == geometry["native_body_byte_delta"]
        and frame.end_byte == geometry["frame_end_byte"],
    }
    return checks, fits, changed, records


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-023-b-copy-sound4-to-sound5"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact", type=Path, default=directory / "derived/analysis-001/capture.symbols.npz"
    )
    args = parser.parse_args()
    registration_path = root / "experiments/sound4-to5-copy-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    source_path, baseline_capture = (
        directory / registration["baseline_artifact"],
        directory / registration["baseline_capture"],
    )
    capture, artifact_path = directory / "capture.wav", args.artifact
    output = root / "experiments/sound4-to5-copy-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, baseline_capture, capture, artifact_path], False
    )
    source, recorded = load_artifact(source_path), load_artifact(artifact_path)
    base, frame = decode_artifact(source), decode_artifact(recorded)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(baseline_capture) != registration["baseline_source_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Baseline or second-owner copy capture differs from registration")
    checks, fits, changed, records = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "second-owner-copy-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "artifact_path": str(artifact_path),
        "decoder_version": recorded.metadata["decoder_version"],
        "decoder_threshold": recorded.metadata["channels"]["left"]["normalized_crossing_threshold"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "changed_selector_ids": changed,
        "destination_records": records,
        "packet_count_delta": len(frame.packets) - len(base.packets),
        "native_body_byte_delta": len(frame.encoded_body) - len(base.encoded_body),
        "native_frame": frame_report(frame),
        "allocation_writer_enabled": False,
        "limits": registration["limits"],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Second-owner copy preservation failed; report retained")


if __name__ == "__main__":
    main()
