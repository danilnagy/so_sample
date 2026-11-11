"""Observe removal versus retained backing when unshared Sound7 is deleted."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data, grouped_packets
from scripts.check_shared_owner_rerecord import payload


def comparison_checks(base, actual, registration):
    expected = registration["control_checks"]
    before, after = grouped_packets(base), grouped_packets(actual)
    old, new = payload(before, 6), payload(after, 6)
    referrers = [key for key in before if len(data := payload(before, key)) >= 9 and data[8] == 6]
    checks = {
        "baseline_packet_count": len(base.packets) == 951,
        "baseline_sound6_empty": not payload(before, 5),
        "baseline_sound7_header_full_payload_and_capacity": old[:9].hex()
        == expected["baseline_sound7_header_hex"]
        and hashlib.sha256(old).hexdigest() == expected["baseline_sound7_payload_sha256"]
        and len(old) == 32777,
        "baseline_owner6_is_unshared": referrers == expected["baseline_owner6_referrers"] == [6],
        "baseline_pattern_identities": all(
            hashlib.sha256(pattern_data(base, n)).hexdigest()
            == expected["pattern_sha256_by_slot"][str(n)]
            for n in range(1, 17)
        ),
        "state_changed_from_baseline": actual.packets != base.packets,
        "selector_order_unchanged": list(before) == list(after) == expected["selector_ids"],
        "all_patterns_unchanged": all(
            pattern_data(base, n) == pattern_data(actual, n) for n in range(1, 17)
        ),
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
    }
    model = registration["empty_record_model"]
    fits = {
        "sound7_record_is_empty": not new,
        "sound6_remains_empty": not payload(after, 5),
        "full_codes_retained_under_owner6": len(new) == len(old)
        and new[:4] == bytes(4)
        and new[8:9] == b"\x06"
        and new[9:] == old[9:],
        "all_other_sound_records_unchanged": all(
            before.get(key) == after.get(key) for key in before.keys() | after.keys() if key != 6
        ),
        "all_non_sound7_plain_packets_unchanged": excluding_destination_data(base, [6])
        == excluding_destination_data(actual, [6]),
        "empty_record_geometry_matches": len(actual.packets) == 815
        and actual.end_byte == 156758
        and len(actual.encoded_body) - len(base.encoded_body) == -33457,
        "entire_empty_record_model_matches": hashlib.sha256(actual.encoded_body).hexdigest()
        == model["body_sha256"],
    }
    observed = {
        "sound7_before_payload_bytes": len(old),
        "sound7_after_payload_bytes": len(new),
        "sound7_after_header_hex": new[:9].hex(),
        "sound7_after_full_payload_sha256": hashlib.sha256(new).hexdigest(),
        "packet_count_delta": len(actual.packets) - len(base.packets),
        "native_body_byte_delta": len(actual.encoded_body) - len(base.encoded_body),
        "changed_selector_ids": sorted(
            key for key in before.keys() | after.keys() if before.get(key) != after.get(key)
        ),
    }
    return checks, fits, observed


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--experiment-dir", type=Path)
    args = parser.parse_args()
    directory = args.experiment_dir or root / "experiments/event-027-b-delete-unshared-sound7"
    artifact_path = args.artifact or directory / "derived/analysis-001/capture.symbols.npz"
    registration_path = (
        directory / "deletion-registration.json"
        if args.experiment_dir
        else root / "experiments/unshared-sound7-deletion-predictions-001.json"
    )
    registration = json.loads(registration_path.read_text())
    source_path, baseline_capture = (
        root / registration["baseline_artifact"],
        root / registration["baseline_capture"],
    )
    capture = directory / "capture.wav"
    output = (
        directory / "hardware-recapture-results-001.json"
        if args.experiment_dir
        else root / "experiments/unshared-sound7-deletion-results-001.json"
    )
    validate_outputs(
        [output], [registration_path, source_path, baseline_capture, capture, artifact_path], False
    )
    source, recorded = load_artifact(source_path), load_artifact(artifact_path)
    base, actual = decode_artifact(source), decode_artifact(recorded)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(baseline_capture) != registration["baseline_source_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Unshared deletion baseline or capture differs from registration")
    checks, fits, observed = comparison_checks(base, actual, registration)
    report = {
        "analysis_version": "unshared-sound7-deletion-control-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "artifact_path": str(artifact_path),
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "observed_deletion": observed,
        "native_frame": frame_report(actual),
        "deletion_writer_enabled": False,
        "limits": registration["limits"],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Unshared Sound7 deletion control failed; report retained")


if __name__ == "__main__":
    main()
