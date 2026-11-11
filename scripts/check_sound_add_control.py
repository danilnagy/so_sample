"""Evaluate the registered Sound2 addition without conflating field hypotheses."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data, pattern_groups, patterns_report
from po33_re.modem.symbols import load_artifact


def comparison_checks(base, frame, registration):
    change = registration["expected_change"]
    pattern, step, sound = change["pattern"], change["step"], change["sound_slot"]
    p = 48 * (step - 1) + 3 * (sound - 1)
    a = 768 + 16 * (step - 1) + sound - 1
    allowed = {*range(p, p + 3), a}
    before, after = pattern_data(base, pattern), pattern_data(frame, pattern)
    byte_changes = [
        {"offset": i, "old": x, "new": y} for i, (x, y) in enumerate(zip(before, after)) if x != y
    ]
    packet_changes = [i for i, (x, y) in enumerate(zip(base.packets, frame.packets)) if x != y]
    rows = patterns_report(frame)["patterns"][pattern - 1]["nonzero_step_rows"]
    slots = next(
        (
            [c["candidate_sound_slot"] for c in r["nonzero_three_byte_cells"]]
            for r in rows
            if r["step"] == step
        ),
        [],
    )
    expected = registration["control_checks"]
    checks = {
        "packet_count": len(base.packets) == len(frame.packets) == expected["packet_count"],
        "frame_end_byte": frame.end_byte == expected["frame_end_byte"],
        "all_packet_checksums": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
        "baseline_target_cell_empty": before[p : p + 3] == bytes(3) and before[a] == 0,
        "new_matching_cell_populated": any(after[p : p + 3]) and after[a] != 0,
        "sample_packets": all(
            x == y for x, y in zip(base.packets, frame.packets) if x.tag in (0x68B5, 0xEF78)
        ),
        "other_patterns": all(
            pattern_data(base, n) == pattern_data(frame, n) for n in range(1, 17) if n != pattern
        ),
        "all_other_plain_packets": bool(packet_changes)
        and set(packet_changes) <= set(pattern_groups(base)[pattern - 1]),
        "populated_steps": [r["step"] for r in rows] == expected["populated_steps"],
        "step1_sound_slots": slots == expected["step1_sound_slots"],
        "locality_and_existing_cells_preserved": bool(byte_changes)
        and all(c["offset"] in allowed for c in byte_changes),
        "footer": before[1024:] == after[1024:],
    }
    hypotheses = registration["separately_evaluated_hypotheses"]
    primary = hypotheses["primary_matches_sound3_key1"]
    begin, end = primary["span"]
    auxiliary = hypotheses["auxiliary_key_index"]
    offset = auxiliary["offset"]
    hypothesis_checks = {
        "primary_matches_sound3_key1": after[begin:end] == bytes.fromhex(primary["expected_hex"]),
        "auxiliary_key_index": before[offset] == auxiliary["old_value"]
        and after[offset] == auxiliary["expected_new_value"],
        "changed_plain_packet_indices": packet_changes
        == hypotheses["changed_plain_packet_indices"],
    }
    return checks, hypothesis_checks, packet_changes, byte_changes, slots


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
        raise ValueError("Baseline source does not match registration")
    if hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]:
        raise ValueError("Baseline body does not match registration")
    if recorded.metadata["source_sha256"] != sha256_file(args.capture):
        raise ValueError("Recorded artifact does not match capture WAV")
    checks, hypotheses, packets, changes, slots = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "registered-sound-add-control-check-0.1",
        "registration_sha256": sha256_file(args.registration),
        "baseline_source_sha256": source.metadata["source_sha256"],
        "capture_sha256": recorded.metadata["source_sha256"],
        "artifact_sha256": sha256_file(args.artifact),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": hypotheses,
        "all_registered_hypotheses_fit": all(hypotheses.values()),
        "changed_plain_packet_indices": packets,
        "pattern1_byte_changes": changes,
        "step1_sound_slots": slots,
        "native_frame": frame_report(frame),
        "user_evidence": "User replied done to the registered Sound2 key1 addition; no deviation reported",
        "hardware_generated_edit_verified": False,
        "limits": [
            "Control invariants and raw-value hypotheses are evaluated separately.",
            "This is a physical note addition, not a generated cell-copy restore or audible polyphony test.",
            "No general Sound2 pitch support or multi-sound writer is enabled by this control alone.",
        ],
    }
    write_bytes(args.out, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Registered Sound2 addition invariants failed; report preserved")


if __name__ == "__main__":
    main()
