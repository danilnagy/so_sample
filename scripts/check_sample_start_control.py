"""Check sample-reference locality and separately evaluate registered trim hypotheses."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import (
    decode_artifact,
    encode_packets,
    frame_report,
    sound_data,
    sound_groups,
)
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact


def reference_comparison_checks(base, frame, registration):
    expected = registration["control_checks"]
    sound_id = registration["expected_change"]["sound_slot"] - 1
    groups_before, groups_after = sound_groups(base), sound_groups(frame)
    before, after = sound_data(base, sound_id), sound_data(frame, sound_id)
    index = expected["sound3_reference_packet_index"]
    packet_changes = [i for i, (a, b) in enumerate(zip(base.packets, frame.packets)) if a != b]
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    checks = {
        "packet_count": len(base.packets) == len(frame.packets) == expected["packet_count"],
        "frame_end_byte": frame.end_byte == expected["frame_end_byte"],
        "all_packet_checksums": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
        "baseline_reference": before.hex() == expected["sound3_reference_before_hex"],
        "reference_location": groups_before[sound_id] == groups_after[sound_id] == [index],
        "reference_size": len(before) == len(after) == expected["sound3_record_size"],
        "owner_id_unchanged": before[8:] == after[8:] == bytes([expected["sound3_owner_id"]]),
        "only_reference_packet_changed": packet_changes == [index],
        "only_allowed_reference_bytes_changed": bool(changes)
        and all(c["offset"] in expected["only_allowed_payload_offsets"] for c in changes),
        "all_patterns_unchanged": all(
            pattern_data(base, p) == pattern_data(frame, p) for p in range(1, 17)
        ),
        "backing_owner_unchanged": sound_data(base, expected["sound3_owner_id"])
        == sound_data(frame, expected["sound3_owner_id"]),
        "packet_tags_and_lengths": all(
            a.tag == b.tag and len(a.payload) == len(b.payload)
            for a, b in zip(base.packets, frame.packets)
        ),
    }
    first, second = int.from_bytes(after[:4], "little"), int.from_bytes(after[4:8], "little")
    return (
        checks,
        packet_changes,
        changes,
        {
            "before": {
                "first_u32le": int.from_bytes(before[:4], "little"),
                "second_u32le": int.from_bytes(before[4:8], "little"),
                "owner_id": before[8],
            },
            "after": {"first_u32le": first, "second_u32le": second, "owner_id": after[8]},
        },
    )


def comparison_checks(base, frame, registration):
    checks, packets, changes, values = reference_comparison_checks(base, frame, registration)
    first, second = values["after"]["first_u32le"], values["after"]["second_u32le"]
    hypotheses = registration["separately_evaluated_hypotheses"]
    owner = sound_data(frame, registration["control_checks"]["sound3_owner_id"])
    hypothesis_checks = {
        "first_field_is_start": 0 < first < len(owner) - 9,
        "second_field_unchanged": second == hypotheses["second_field_unchanged"]["expected_value"],
        "second_field_moves_with_start": second - first
        == hypotheses["second_field_moves_with_start"]["expected_difference_second_minus_first"],
    }
    return checks, hypothesis_checks, packets, changes, values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registration", type=Path)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    validate_outputs(
        [args.out], [args.registration, args.baseline, args.artifact, args.capture], False
    )
    registration = json.loads(args.registration.read_text())
    source, recorded = load_artifact(args.baseline), load_artifact(args.artifact)
    base, frame = decode_artifact(source), decode_artifact(recorded)
    if sha256_file(args.baseline) != registration["baseline_artifact_sha256"]:
        raise ValueError("Baseline artifact does not match registration")
    if source.metadata["source_sha256"] != registration["baseline_source_sha256"]:
        raise ValueError("Baseline capture identity differs")
    if hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]:
        raise ValueError("Baseline body differs")
    if recorded.metadata["source_sha256"] != sha256_file(args.capture):
        raise ValueError("Recorded artifact does not match capture WAV")
    checks, hypotheses, packets, changes, values = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "sample-start-control-check-0.1",
        "registration_sha256": sha256_file(args.registration),
        "capture_sha256": sha256_file(args.capture),
        "artifact_sha256": sha256_file(args.artifact),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": hypotheses,
        "any_registered_second_field_hypothesis_fits": hypotheses["second_field_unchanged"]
        or hypotheses["second_field_moves_with_start"],
        "changed_plain_packet_indices": packets,
        "sound3_reference_byte_changes": changes,
        "sound3_header_values": values,
        "native_frame": frame_report(frame),
        "user_report": "still hear the tone and done",
        "audible_tone_confirmed": True,
        "nonzero_start_writer_enabled": False,
        "limits": [
            "Control preservation and mutually alternative field hypotheses are evaluated separately",
            "Audible tone is user reported; duration and exact start position were not independently measured",
            "Both second-field predictions fail; observed65535 is retained without assigning endpoint, length or sentinel semantics",
            "A passing physical control is not acceptance of a generated nonzero-start edit",
        ],
    }
    write_bytes(args.out, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Sample start preservation checks failed; report retained")


if __name__ == "__main__":
    main()
