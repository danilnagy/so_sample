"""Compare a nine-page Sound6 restore with exact, rounded and truncated capacities."""

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
    before, expected, after = (
        grouped_packets(base),
        grouped_packets(target),
        grouped_packets(actual),
    )
    supplied, restored = payload(expected, 5), payload(after, 5)
    target_window, _ = zero_start_window(expected, 5)
    actual_window, actual_view = zero_start_window(after, 5)
    capacity = (
        len(restored) - 9
        if len(restored) > 9 and restored[:4] == bytes(4) and restored[8] == 5
        else None
    )
    checks = {
        "baseline_body_matches": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "baseline_sound6_and7_empty": not payload(before, 5) and not payload(before, 6),
        "state_changed_from_baseline": actual.packets != base.packets,
        "sound6_record_present": bool(restored),
        "selector_order_unchanged": list(before) == list(after),
        "all_patterns_unchanged": all(
            pattern_data(base, n) == pattern_data(actual, n) for n in range(1, 17)
        ),
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
    }
    fits = {
        "exact_nine_page_capacity36864": capacity == 36864,
        "rounded_ten_page_capacity40960": capacity == 40960,
        "unused_page_dropped_capacity32768": capacity == 32768,
        "original_header_and32768_code_prefix_preserved": capacity is not None
        and capacity >= 32768
        and restored[:32777] == supplied[:32777],
        "entire_supplied36864_code_prefix_preserved": capacity is not None
        and capacity >= 36864
        and restored[:36873] == supplied,
        "logical_window_preserved": target_window is not None
        and actual_window is not None
        and target_window == actual_window,
        "all_non_sound6_plain_packets_unchanged": excluding_destination_data(base, [5])
        == excluding_destination_data(actual, [5]),
        "sound7_remains_empty": not payload(after, 6),
        "ordered4096_page_packet_layout_matches": capacity is not None
        and capacity >= 4096
        and capacity % 4096 == 0
        and [len(p.payload) for p in after.get(5, ())]
        == [255] * 16 + [25] + ([255] * 16 + [16]) * (capacity // 4096 - 1),
        "entire_generated_native_body_matches": actual.encoded_body == target.encoded_body,
    }
    observed = {
        "sound6_capacity_codes": capacity,
        "sound6_payload_bytes": len(restored),
        "sound6_header_hex": restored[:9].hex(),
        "sound6_payload_sha256": hashlib.sha256(restored).hexdigest(),
        "sound6_window": actual_view,
        "packet_count": len(actual.packets),
        "frame_end_byte": actual.end_byte,
    }
    return checks, fits, observed


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-sound6-nine-pages-001"
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
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Registered source, odd-page candidate or recapture identity differs")
    base, target, actual = (
        decode_artifact(load_artifact(source_path)),
        decode_artifact(load_artifact(target_path)),
        decode_artifact(recorded),
    )
    checks, fits, observed = comparison_checks(base, target, actual, registration)
    report = {
        "analysis_version": "odd-nine-page-sound6-restore-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(args.artifact),
        "artifact_path": str(args.artifact),
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "observed_capacity": observed,
        "native_frame": frame_report(actual),
        "limits": registration["limits"],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Odd-page restore control failed; report retained")


if __name__ == "__main__":
    main()
