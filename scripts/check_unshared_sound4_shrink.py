"""Observe capacity shrink versus reuse when an unshared Sound4 is re-recorded."""

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


def comparison_checks(base, frame, registration):
    expected = registration["control_checks"]
    before, after = grouped_packets(base), grouped_packets(frame)
    old4, new4 = payload(before, 3), payload(after, 3)
    before_codes, before_view = zero_start_window(before, 3)
    after_codes, after_view = zero_start_window(after, 3)
    referrers = [key for key in before if len(data := payload(before, key)) >= 9 and data[8] == 3]
    checks = {
        "baseline_packet_count": len(base.packets) == expected["baseline_packet_count"],
        "baseline_sound4_header_payload_and_capacity": old4[:9].hex()
        == expected["baseline_sound4_header_hex"]
        and hashlib.sha256(old4).hexdigest() == expected["baseline_sound4_payload_sha256"]
        and len(old4) - 9 == expected["baseline_sound4_code_count"],
        "baseline_sound5_payload": hashlib.sha256(payload(before, 4)).hexdigest()
        == expected["baseline_sound5_payload_sha256"],
        "baseline_owner3_is_unshared": referrers == expected["baseline_owner3_referrers"] == [3],
        "baseline_pattern_identities": all(
            hashlib.sha256(pattern_data(base, n)).hexdigest()
            == expected["pattern_sha256_by_slot"][str(n)]
            for n in range(1, 17)
        ),
        "sound4_record_changed": before.get(3) != after.get(3),
        "sound4_record_present": bool(new4),
        "selector_order_unchanged": list(before) == list(after) == expected["selector_ids"],
        "all_patterns_unchanged": all(
            pattern_data(base, n) == pattern_data(frame, n) for n in range(1, 17)
        ),
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
    }
    hypotheses = registration["separately_evaluated_hypotheses"]
    capacity = after_view.get("backing_code_count")
    fits = {
        "new_sound4_window_is_zero_start_owner3": after_view["resolved"]
        and after_view["owner_id"] == 3,
        "new_sound4_logical_codes_differ": before_codes is not None
        and after_codes is not None
        and after_codes != before_codes,
        "new_sound4_endpoint_is_smaller": after_view["resolved"]
        and after_view["endpoint"]
        < hypotheses["new_sound4_endpoint_is_smaller"]["maximum_exclusive"],
        "new_sound4_backing_capacity_shrinks": capacity is not None
        and capacity < hypotheses["new_sound4_backing_capacity_shrinks"]["maximum_exclusive"],
        "new_sound4_backing_capacity_is_reused": capacity
        == hypotheses["new_sound4_backing_capacity_is_reused"]["expected_value"],
        "sound5_full_buffer_and_header_preserved": payload(before, 4) == payload(after, 4),
        "all_other_sound_records_unchanged": all(
            before.get(key) == after.get(key) for key in before.keys() | after.keys() if key != 3
        ),
        "all_non_sound4_plain_packets_unchanged": excluding_destination_data(base, [3])
        == excluding_destination_data(frame, [3]),
        "new_backing_capacity_multiple4096": capacity is not None
        and capacity > 0
        and capacity % 4096 == 0,
        "new_backing_capacity_multiple8192": capacity is not None
        and capacity > 0
        and capacity % 8192 == 0,
    }
    changed = sorted(
        key for key in before.keys() | after.keys() if before.get(key) != after.get(key)
    )
    records = []
    for key in changed:
        record = {"selector_id": key}
        for label, groups in (("before", before), ("after", after)):
            data = payload(groups, key)
            info = {
                "payload_bytes": len(data),
                "packet_count": len(groups.get(key, ())),
                "payload_sha256": hashlib.sha256(data).hexdigest(),
            }
            if len(data) >= 9:
                info.update(
                    header_hex=data[:9].hex(),
                    first_u32le=int.from_bytes(data[:4], "little"),
                    second_u32le=int.from_bytes(data[4:8], "little"),
                    owner_id=data[8],
                    bytes_after_header=len(data) - 9,
                )
            record[label] = info
        records.append(record)
    observed = {
        "sound4_before_window": before_view,
        "sound4_after_window": after_view,
        "packet_count_delta": len(frame.packets) - len(base.packets),
        "native_body_byte_delta": len(frame.encoded_body) - len(base.encoded_body),
    }
    return checks, fits, changed, records, observed


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-025-b-rerecord-unshared-sound4-short"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact", type=Path, default=directory / "derived/analysis-001/capture.symbols.npz"
    )
    args = parser.parse_args()
    registration_path = root / "experiments/unshared-sound4-shrink-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    source_path, baseline_capture = (
        directory / registration["baseline_artifact"],
        directory / registration["baseline_capture"],
    )
    capture, artifact_path = directory / "capture.wav", args.artifact
    tone = directory / registration["source_tone"]["path"]
    output = root / "experiments/unshared-sound4-shrink-results-001.json"
    validate_outputs(
        [output],
        [registration_path, source_path, baseline_capture, capture, artifact_path, tone],
        False,
    )
    source, recorded = load_artifact(source_path), load_artifact(artifact_path)
    base, frame = decode_artifact(source), decode_artifact(recorded)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(baseline_capture) != registration["baseline_source_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
        or sha256_file(tone) != registration["source_tone"]["wav_sha256"]
    ):
        raise ValueError("Baseline, shorter re-recording or source tone differs from registration")
    checks, fits, changed, records, observed = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "first-unshared-owner-shrink-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "artifact_path": str(artifact_path),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "changed_selector_ids": changed,
        "changed_sound_records": records,
        "observed_allocation": observed,
        "native_frame": frame_report(frame),
        "allocation_writer_enabled": False,
        "limits": registration["limits"],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Unshared shorter re-recording control failed; report retained")


if __name__ == "__main__":
    main()
