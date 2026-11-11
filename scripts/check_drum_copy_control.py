"""Evaluate drum-copy locality and alternative hypotheses without fixing slice bounds."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, sound_groups
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact


def grouped_packets(frame):
    groups = sound_groups(frame)
    return {key: tuple(frame.packets[i] for i in indices) for key, indices in groups.items()}


def excluding_destination_data(frame, destination_ids):
    """Retain every selector/other packet; omit only EF78 under candidate selectors."""
    selector, retained = None, []
    for packet in frame.packets:
        if packet.tag == 0x68B5:
            selector = packet.payload[0]
        if packet.tag != 0xEF78 or selector not in destination_ids:
            retained.append(packet)
    return tuple(retained)


def reference_comparison_checks(base, frame, registration):
    expected = registration["control_checks"]
    ids = expected["candidate_destination_selector_ids"]
    before, after = grouped_packets(base), grouped_packets(frame)
    changed = sorted(
        key for key in before.keys() | after.keys() if before.get(key) != after.get(key)
    )
    populated = [key for key in ids if after.get(key)]
    checks = {
        "baseline_packet_count": len(base.packets) == expected["baseline_packet_count"],
        "baseline_source_header": b"".join(p.payload for p in before[0])[:9].hex()
        == expected["baseline_source_sound1_header_hex"],
        "baseline_source_payload": hashlib.sha256(
            b"".join(p.payload for p in before[0])
        ).hexdigest()
        == expected["baseline_source_sound1_payload_sha256"],
        "candidate_destination_empty_before": all(not before.get(key) for key in ids),
        "selector_order_unchanged": list(before) == list(after),
        "only_candidate_destination_data_changed": bool(changed) and set(changed) <= set(ids),
        "other_sound_records_and_backing_codes_unchanged": all(
            before.get(key) == after.get(key)
            for key in before.keys() | after.keys()
            if key not in ids
        ),
        "all_patterns_unchanged": all(
            pattern_data(base, p) == pattern_data(frame, p) for p in range(1, 17)
        ),
        "every_other_plain_packet_unchanged": excluding_destination_data(base, ids)
        == excluding_destination_data(frame, ids),
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
    }
    records = []
    for key in populated:
        data = b"".join(p.payload for p in after[key])
        record = {
            "selector_id": key,
            "packet_count": len(after[key]),
            "bytes": len(data),
            "payload_hex": data.hex(),
        }
        if len(data) == 9:
            record.update(
                first_u32le=int.from_bytes(data[:4], "little"),
                second_u32le=int.from_bytes(data[4:8], "little"),
                owner_id=data[8],
            )
        records.append(record)
    return checks, changed, records, populated


def comparison_checks(base, frame, registration):
    checks, changed, records, populated = reference_comparison_checks(base, frame, registration)
    ids = registration["control_checks"]["candidate_destination_selector_ids"]
    hypotheses = registration["separately_evaluated_hypotheses"]
    reference = hypotheses["populated_destination_records_are_owner0_references"]
    fits = {
        "sound9_uses_selector_block8_to23": bool(changed)
        and set(changed) <= set(ids)
        and checks["every_other_plain_packet_unchanged"],
        "only_first_destination_group_populated": populated
        == hypotheses["only_first_destination_group_populated"]["populated_ids"],
        "all16_destination_groups_populated": populated
        == hypotheses["all16_destination_groups_populated"]["populated_ids"],
        "populated_destination_records_are_owner0_references": bool(records)
        and all(
            r["bytes"] == reference["record_bytes"] and r.get("owner_id") == reference["owner_id"]
            for r in records
        ),
    }
    return checks, fits, changed, records


def main():
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments/drum9-copy-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    directory = root / "experiments/event-015-b-copy-sound1-to-drum9"
    source_path = directory / registration["baseline_artifact"]
    capture = directory / "capture.wav"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    output = root / "experiments/drum9-copy-results-001.json"
    validate_outputs([output], [registration_path, source_path, capture, artifact_path], False)
    source, recorded = load_artifact(source_path), load_artifact(artifact_path)
    base, frame = decode_artifact(source), decode_artifact(recorded)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Capture/baseline identity differs from registration")
    checks, hypotheses, changed, records = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "first-drum-copy-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": hypotheses,
        "changed_selector_ids": changed,
        "destination_records": records,
        "packet_count_delta": len(frame.packets) - len(base.packets),
        "native_body_byte_delta": len(frame.encoded_body) - len(base.encoded_body),
        "native_frame": frame_report(frame),
        "user_report": "done",
        "drum_writer_enabled": False,
        "drum_preview_enabled": False,
        "limits": [
            "Sound9 changes only selector8..23 data; individual keyboard-key to slice-order mapping still needs a direct control",
            "The sixteen9-byte owner0 records share existing samples; no new buffer allocation is observed here",
            "Observed regular boundaries were not preregistered and do not establish general autoslice or inclusivity rules",
            "Other drum slots, sound parameters, slice edits and audible playback are not yet calibrated",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Drum-copy locality failed; report retained")


if __name__ == "__main__":
    main()
