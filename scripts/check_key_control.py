"""Evaluate a registered fixed-step keyboard control with separate hypotheses."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data, pattern_groups, patterns_report
from po33_re.modem.symbols import load_artifact


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
    if source.metadata["source_sha256"] != registration["baseline_source_sha256"]:
        raise ValueError("Baseline source does not match registration")
    if hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]:
        raise ValueError("Baseline body does not match registration")
    if recorded.metadata["source_sha256"] != sha256_file(args.capture):
        raise ValueError("Recorded artifact does not match capture WAV")
    change = registration["expected_change"]
    pattern, step, sound = change["pattern"], change["step"], change["sound_slot"]
    primary_offset = 48 * (step - 1) + 3 * (sound - 1)
    auxiliary_offset = 768 + 16 * (step - 1) + sound - 1
    allowed_bytes = {*range(primary_offset, primary_offset + 3), auxiliary_offset}
    before, after = pattern_data(base, pattern), pattern_data(frame, pattern)
    byte_changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packet_changes = [i for i, (a, b) in enumerate(zip(base.packets, frame.packets)) if a != b]
    steps = [
        r["step"] for r in patterns_report(frame)["patterns"][pattern - 1]["nonzero_step_rows"]
    ]
    expected = registration["control_checks"]
    checks = {
        "packet_count": len(base.packets) == len(frame.packets) == expected["packet_count"],
        "frame_end_byte": frame.end_byte == expected["frame_end_byte"],
        "all_packet_checksums": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
        "sample_packets": all(
            a == b for a, b in zip(base.packets, frame.packets) if a.tag in (0x68B5, 0xEF78)
        ),
        "other_patterns": all(
            pattern_data(base, p) == pattern_data(frame, p) for p in range(1, 17) if p != pattern
        ),
        "all_other_plain_packets": bool(packet_changes)
        and set(packet_changes) <= set(pattern_groups(base)[pattern - 1]),
        "populated_steps": steps == expected["populated_steps"],
        "changed_cell": bool(byte_changes)
        and any(c["offset"] in allowed_bytes for c in byte_changes),
        "locality": all(c["offset"] in allowed_bytes for c in byte_changes),
    }
    hypotheses = registration["separately_evaluated_hypotheses"]
    primary = hypotheses["primary_stays_unchanged"]
    begin, end = primary["span"]
    auxiliary = hypotheses["auxiliary_key_index"]
    offset = auxiliary["offset"]
    hypothesis_checks = {
        "primary_stays_unchanged": before[begin:end]
        == after[begin:end]
        == bytes.fromhex(primary["expected_hex"]),
        "auxiliary_key_index": before[offset] == auxiliary["old_value"]
        and after[offset] == auxiliary["expected_new_value"],
    }
    report = {
        "analysis_version": "registered-key-control-check-0.1",
        "registration_sha256": sha256_file(args.registration),
        "baseline_source_sha256": source.metadata["source_sha256"],
        "capture_sha256": recorded.metadata["source_sha256"],
        "artifact_sha256": sha256_file(args.artifact),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": hypothesis_checks,
        "all_registered_hypotheses_fit": all(hypothesis_checks.values()),
        "changed_plain_packet_indices": packet_changes,
        "pattern1_byte_changes": byte_changes,
        "native_frame": frame_report(frame),
        "user_evidence": "User completion report for the registered physical control; exact buttons and pitch were not independently observed",
        "limits": [
            "Control invariants and field hypotheses are evaluated separately; no failed hypothesis is reclassified as a pass.",
            "A physical key control is not acceptance of a generated key edit or every intermediate keyboard value.",
            "Measured-clock decoding, when used, is independent of these expected byte values.",
        ],
    }
    write_bytes(args.out, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Registered control invariants failed; complete report retained")


if __name__ == "__main__":
    main()
