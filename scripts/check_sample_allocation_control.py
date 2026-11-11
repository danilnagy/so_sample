"""Observe a new Sound4 recording without assuming allocation geometry or ownership."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, sound_groups
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data, grouped_packets


def comparison_checks(base, frame, registration):
    expected = registration["control_checks"]
    selector = registration["expected_change"]["selector_id"]
    before, after = grouped_packets(base), grouped_packets(frame)
    changed = sorted(
        key for key in before.keys() | after.keys() if before.get(key) != after.get(key)
    )
    old_owner = b"".join(p.payload for p in before.get(0, ()))
    new_owner = b"".join(p.payload for p in after.get(0, ()))
    data = b"".join(p.payload for p in after.get(selector, ()))
    checks = {
        "baseline_packet_count": len(base.packets) == expected["baseline_packet_count"],
        "baseline_owner0_header": old_owner[:9].hex() == expected["baseline_owner0_header_hex"],
        "baseline_owner0_payload": hashlib.sha256(old_owner).hexdigest()
        == expected["baseline_owner0_payload_sha256"],
        "baseline_target_empty": not before.get(selector),
        "target_sound4_data_present": bool(data),
        "selector_order_unchanged": list(before) == list(after) == expected["selector_ids"],
        "baseline_pattern_identities": all(
            hashlib.sha256(pattern_data(base, n)).hexdigest()
            == expected["pattern_sha256_by_slot"][str(n)]
            for n in range(1, 17)
        ),
        "all_patterns_unchanged": all(
            pattern_data(base, n) == pattern_data(frame, n) for n in range(1, 17)
        ),
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
    }
    fields = None
    if len(data) >= 9:
        fields = {
            "first_u32le": int.from_bytes(data[:4], "little"),
            "second_u32le": int.from_bytes(data[4:8], "little"),
            "owner_id": data[8],
        }
    hypotheses = registration["separately_evaluated_hypotheses"]
    owner_hypothesis = hypotheses["sound4_record_is_self_owned_buffer"]
    count_delta = len(frame.packets) - len(base.packets)
    other_sounds_preserved = all(
        before.get(key) == after.get(key) for key in before.keys() | after.keys() if key != selector
    )
    fits = {
        "sound4_record_is_self_owned_buffer": fields is not None
        and len(data) > owner_hypothesis["minimum_payload_bytes_exclusive"]
        and fields["owner_id"] == owner_hypothesis["owner_id"],
        "sound4_reference_is_zero_start": fields is not None
        and fields["first_u32le"] == hypotheses["sound4_reference_is_zero_start"]["expected_value"],
        "sound4_endpoint_within_new_buffer": fields is not None
        and 0 < fields["second_u32le"] <= len(data) - 9,
        "only_sound4_data_group_changes": changed
        == hypotheses["only_sound4_data_group_changes"]["expected_changed_selector_ids"],
        "existing_owner0_header_and_codes_unchanged": old_owner == new_owner,
        "all_other_sound_records_unchanged": other_sounds_preserved,
        "only_sound4_data_packets_added": excluding_destination_data(base, [selector])
        == excluding_destination_data(frame, [selector])
        and count_delta == len(after.get(selector, ()))
        and count_delta > 0,
        "new_sample_codes_differ_from_existing_owner0": len(data) > 9 and data[9:] != old_owner[9:],
    }
    records = []
    groups_before, groups_after = sound_groups(base), sound_groups(frame)
    for key in changed:
        old = b"".join(p.payload for p in before.get(key, ()))
        new = b"".join(p.payload for p in after.get(key, ()))
        record = {
            "selector_id": key,
            "before_payload_bytes": len(old),
            "after_payload_bytes": len(new),
            "before_payload_sha256": hashlib.sha256(old).hexdigest(),
            "after_payload_sha256": hashlib.sha256(new).hexdigest(),
            "before_packet_indices": groups_before.get(key, []),
            "after_packet_indices": groups_after.get(key, []),
        }
        for label, payload in (("before", old), ("after", new)):
            if len(payload) >= 9:
                record[label + "_raw_header"] = {
                    "hex": payload[:9].hex(),
                    "first_u32le": int.from_bytes(payload[:4], "little"),
                    "second_u32le": int.from_bytes(payload[4:8], "little"),
                    "owner_id": payload[8],
                    "bytes_after_header": len(payload) - 9,
                }
        records.append(record)
    observed = {
        "sound4_payload_bytes": len(data),
        "sound4_packet_count": len(after.get(selector, ())),
        "sound4_raw_fields": fields,
        "packet_count_delta": count_delta,
        "native_body_byte_delta": len(frame.encoded_body) - len(base.encoded_body),
        "owner0_before_bytes": len(old_owner),
        "owner0_after_bytes": len(new_owner),
        "non_sound4_plain_packet_sequence_unchanged": excluding_destination_data(base, [selector])
        == excluding_destination_data(frame, [selector]),
    }
    return checks, fits, changed, records, observed


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-022-b-record-independent-sound4"
    registration_path = root / "experiments/sound4-allocation-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    source_path, baseline_capture = (
        directory / registration["baseline_artifact"],
        directory / registration["baseline_capture"],
    )
    capture, artifact_path = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    tone = directory / registration["source_tone"]["path"]
    output = root / "experiments/sound4-allocation-results-001.json"
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
        raise ValueError("Baseline, allocation capture or input tone differs from registration")
    checks, fits, changed, records, observed = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "second-independent-owner-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
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
        raise ValueError(
            "Allocation capture/control identity or pattern preservation failed; report retained"
        )


if __name__ == "__main__":
    main()
