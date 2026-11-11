"""Compare the one-page ordinary-WAV import with the exact supplied sample."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data, grouped_packets
from scripts.check_shared_owner_rerecord import payload, zero_start_window


def comparison_checks(base, target, actual, registration):
    before, supplied, after = (
        grouped_packets(base),
        grouped_packets(target),
        grouped_packets(actual),
    )
    old, expected, new = payload(before, 5), payload(supplied, 5), payload(after, 5)
    target_window, _ = zero_start_window(supplied, 5)
    actual_window, view = zero_start_window(after, 5)
    capacity = len(new) - 9 if len(new) > 9 and new[:4] == bytes(4) and new[8] == 5 else None
    checks = {
        "baseline_body_matches": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "baseline_sound6_nine_page_owner": len(old) == 36873
        and old[:9].hex() == "00000000c078000005",
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "state_changed_from_baseline": actual.packets != base.packets,
        "sound6_record_present": bool(new),
        "selector_order_unchanged": list(before) == list(after),
        "all_patterns_unchanged": all(
            pattern_data(base, n) == pattern_data(actual, n) for n in range(1, 17)
        ),
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
    }
    fits = {
        "exact_one_page_capacity4096": capacity == 4096,
        "larger_buffer_capacity": capacity is not None and capacity > 4096,
        "header_matches2344_endpoint": new[:9].hex() == registration["expected_sound6_header_hex"],
        "all_supplied4096_codes_preserved": capacity is not None
        and capacity >= 4096
        and new[9:4105] == expected[9:],
        "imported2344_code_prefix_preserved": capacity is not None
        and capacity >= 2344
        and new[9:2353] == expected[9:2353],
        "imported2344_code_window_preserved": target_window is not None
        and actual_window is not None
        and target_window == actual_window,
        "all_non_sound6_plain_packets_unchanged": excluding_destination_data(base, [5])
        == excluding_destination_data(actual, [5]),
        "sound7_remains_empty": not payload(after, 6),
        "entire_generated_native_body_matches": actual.encoded_body == target.encoded_body,
    }
    observed = {
        "sound6_capacity_codes": capacity,
        "sound6_payload_bytes": len(new),
        "sound6_header_hex": new[:9].hex(),
        "sound6_payload_sha256": hashlib.sha256(new).hexdigest(),
        "sound6_window": view,
        "packet_count": len(actual.packets),
        "frame_end_byte": actual.end_byte,
    }
    return checks, fits, observed


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-sound6-one-page-import-001"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact", type=Path, default=directory / "derived/analysis-001/capture.symbols.npz"
    )
    args = parser.parse_args()
    registration_path = directory / "restore-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path, target_path = (
        root / registration["source_artifact"],
        directory / "edited.symbols.npz",
    )
    capture = directory / "capture.wav"
    output = directory / "hardware-recapture-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, target_path, capture, args.artifact], False
    )
    recorded = load_artifact(args.artifact)
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(target_path) != registration["edited_artifact_sha256"]
        or sha256_file(directory / "restore.wav") != registration["restore_wav_sha256"]
        or sha256_file(directory / "software-validation.json")
        != registration["software_validation_sha256"]
        or sha256_file(directory / "input-sample.wav") != registration["input_wav_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Registered source, imported WAV or recapture identity differs")
    base, target, actual = (
        decode_artifact(load_artifact(source_path)),
        decode_artifact(load_artifact(target_path)),
        decode_artifact(recorded),
    )
    checks, fits, observed = comparison_checks(base, target, actual, registration)
    report = {
        "analysis_version": "one-page-Sound6-import-recapture-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(args.artifact),
        "artifact_path": str(args.artifact),
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "observed_import": observed,
        "native_frame": frame_report(actual),
        "limits": registration["limits"],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("One-page import control failed; report retained")


if __name__ == "__main__":
    main()
