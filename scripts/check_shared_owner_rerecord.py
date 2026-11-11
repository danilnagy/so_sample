"""Observe shared-sample overwrite without assuming copy-on-write or allocation sizes."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data, grouped_packets


def payload(groups, selector):
    return b"".join(packet.payload for packet in groups.get(selector, ()))


def zero_start_window(groups, selector):
    """Research-only resolution; report unknown layouts without guessing samples."""
    record = payload(groups, selector)
    if len(record) < 9 or record[:4] != bytes(4):
        return None, {"resolved": False, "reason": "Missing or nonzero-start record"}
    owner_id = record[8]
    owner = payload(groups, owner_id)
    if len(owner) <= 9 or owner[:4] != bytes(4) or owner[8] != owner_id:
        return None, {
            "resolved": False,
            "reason": "Missing or unobserved backing-owner layout",
            "owner_id": owner_id,
        }
    endpoint = int.from_bytes(record[4:8], "little")
    if not 0 < endpoint <= len(owner) - 9:
        return None, {
            "resolved": False,
            "reason": "Endpoint exceeds backing data",
            "owner_id": owner_id,
        }
    codes = owner[9 : 9 + endpoint]
    return codes, {
        "resolved": True,
        "owner_id": owner_id,
        "endpoint": endpoint,
        "backing_code_count": len(owner) - 9,
        "logical_codes_sha256": hashlib.sha256(codes).hexdigest(),
    }


def comparison_checks(base, frame, registration):
    expected = registration["control_checks"]
    before, after = grouped_packets(base), grouped_packets(frame)
    old4, old5 = payload(before, 3), payload(before, 4)
    new4, new5 = payload(after, 3), payload(after, 4)
    before4, before4_view = zero_start_window(before, 3)
    before5, before5_view = zero_start_window(before, 4)
    after4, after4_view = zero_start_window(after, 3)
    after5, after5_view = zero_start_window(after, 4)
    checks = {
        "baseline_packet_count": len(base.packets) == expected["baseline_packet_count"],
        "baseline_sound4_payload": hashlib.sha256(old4).hexdigest()
        == expected["baseline_sound4_payload_sha256"],
        "baseline_sound4_header_and_capacity": old4[:9].hex()
        == expected["baseline_sound4_header_hex"]
        and len(old4) - 9 == expected["baseline_backing_code_count"],
        "baseline_sound5_reference": old5.hex() == expected["baseline_sound5_reference_hex"],
        "baseline_pattern_identities": all(
            hashlib.sha256(pattern_data(base, n)).hexdigest()
            == expected["pattern_sha256_by_slot"][str(n)]
            for n in range(1, 17)
        ),
        "baseline_copy_shares_source_window": before4 is not None and before4 == before5,
        "source_sound4_record_changed": before.get(3) != after.get(3),
        "source_sound4_data_present": bool(new4),
        "selector_order_unchanged": list(before) == list(after) == expected["selector_ids"],
        "all_patterns_unchanged": all(
            pattern_data(base, n) == pattern_data(frame, n) for n in range(1, 17)
        ),
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
    }
    hypotheses = registration["separately_evaluated_hypotheses"]
    transfer = hypotheses["old_full_buffer_transferred_to_self_owned_sound5"]
    fits = {
        "new_sound4_record_is_zero_start": len(new4) >= 9 and new4[:4] == bytes(4),
        "new_sound4_record_has_different_logical_codes": after4 is not None
        and before4 is not None
        and after4 != before4,
        "new_sound4_backing_buffer_is_larger": after4_view["resolved"]
        and after4_view["backing_code_count"]
        > hypotheses["new_sound4_backing_buffer_is_larger"]["minimum_code_count_exclusive"],
        "sound5_record_remains_present": bool(new5),
        "sound5_logical_sample_window_preserved": before5 is not None and after5 == before5,
        "old_full_buffer_transferred_to_self_owned_sound5": len(new5) == 9 + transfer["code_count"]
        and new5[:8] == old4[:8]
        and new5[8] == transfer["owner_id"]
        and new5[9:] == old4[9:],
        "sound5_reference_unchanged_and_tracks_new_sound4": new5 == old5
        and after5 is not None
        and after4 is not None
        and after5 != before5
        and len(after5) <= len(after4)
        and after5 == after4[: len(after5)],
        "existing_owner0_header_and_codes_unchanged": payload(before, 0) == payload(after, 0),
        "all_sound_records_outside_sound4_and5_unchanged": all(
            before.get(key) == after.get(key)
            for key in before.keys() | after.keys()
            if key not in (3, 4)
        ),
        "all_other_plain_packets_unchanged": excluding_destination_data(base, [3, 4])
        == excluding_destination_data(frame, [3, 4]),
    }
    changed = sorted(
        key for key in before.keys() | after.keys() if before.get(key) != after.get(key)
    )
    records = []
    for selector in changed:
        item = {"selector_id": selector}
        for label, groups in (("before", before), ("after", after)):
            data = payload(groups, selector)
            info = {
                "payload_bytes": len(data),
                "packet_count": len(groups.get(selector, ())),
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
            item[label] = info
        records.append(item)
    observed = {
        "sound4_before_window": before4_view,
        "sound5_before_window": before5_view,
        "sound4_after_window": after4_view,
        "sound5_after_window": after5_view,
        "packet_count_delta": len(frame.packets) - len(base.packets),
        "native_body_byte_delta": len(frame.encoded_body) - len(base.encoded_body),
    }
    return checks, fits, changed, records, observed


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-024-b-rerecord-shared-sound4"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact", type=Path, default=directory / "derived/analysis-001/capture.symbols.npz"
    )
    args = parser.parse_args()
    registration_path = root / "experiments/shared-sound4-rerecord-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    source_path, baseline_capture = (
        directory / registration["baseline_artifact"],
        directory / registration["baseline_capture"],
    )
    capture, artifact_path = directory / "capture.wav", args.artifact
    tone = directory / registration["source_tone"]["path"]
    output = root / "experiments/shared-sound4-rerecord-results-001.json"
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
        raise ValueError("Baseline, re-recording capture or source tone differs from registration")
    checks, fits, changed, records, observed = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "first-shared-owner-rerecord-check-0.1",
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
        "observed_ownership": observed,
        "native_frame": frame_report(frame),
        "allocation_writer_enabled": False,
        "limits": registration["limits"],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Shared-owner re-recording control failed; report retained")


if __name__ == "__main__":
    main()
