"""Evaluate the fixed-step key2 control without conflating hypotheses and invariants."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data, pattern_groups, patterns_report
from po33_re.modem.symbols import load_artifact


def main():
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments/melodic-key2-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    base_path = root / "experiments/edited-pattern-001/derived/analysis-001/capture.symbols.npz"
    directory = root / "experiments/event-008-b-melodic-key2"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    source, artifact = [load_artifact(p) for p in (base_path, artifact_path)]
    base, frame = [decode_artifact(a) for a in (source, artifact)]
    if source.metadata["source_sha256"] != registration["baseline_source_sha256"]:
        raise ValueError("Baseline source hash does not match registration")
    if hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]:
        raise ValueError("Baseline body does not match registration")
    if artifact.metadata["source_sha256"] != sha256_file(capture):
        raise ValueError("New artifact does not match capture WAV")
    a, b = pattern_data(base, 1), pattern_data(frame, 1)
    changes = [i for i, (x, y) in enumerate(zip(base.packets, frame.packets)) if x != y]
    allowed_packets = set(pattern_groups(base)[0])
    byte_changes = [
        {"offset": i, "old": x, "new": y} for i, (x, y) in enumerate(zip(a, b)) if x != y
    ]
    allowed_bytes = {198, 199, 200, 834}
    rows = patterns_report(frame)["patterns"][0]["nonzero_step_rows"]
    steps = [row["step"] for row in rows]
    checks = {
        "packet_count": len(base.packets) == len(frame.packets) == 511,
        "frame_end_byte": frame.end_byte == 89396,
        "all_packet_checksums": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
        "sample_packets": all(
            x == y for x, y in zip(base.packets, frame.packets) if x.tag in (0x68B5, 0xEF78)
        ),
        "other_patterns": all(
            pattern_data(base, p) == pattern_data(frame, p) for p in range(2, 17)
        ),
        "all_other_plain_packets": bool(changes) and set(changes) <= allowed_packets,
        "populated_steps": steps == [1, 5, 9, 13],
        "changed_cell": bool(byte_changes)
        and any(c["offset"] in allowed_bytes for c in byte_changes),
        "locality": all(c["offset"] in allowed_bytes for c in byte_changes),
    }
    hypotheses = {
        "primary_stays_unchanged": a[198:201] == b[198:201] == bytes.fromhex("0df883"),
        "auxiliary_key_index": a[834] == 240 and b[834] == 241,
    }
    report = {
        "analysis_version": "native-melodic-key2-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "baseline_source_sha256": source.metadata["source_sha256"],
        "capture_sha256": artifact.metadata["source_sha256"],
        "artifact_sha256": sha256_file(artifact_path),
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": hypotheses,
        "all_registered_hypotheses_fit": all(hypotheses.values()),
        "changed_plain_packet_indices": changes,
        "pattern1_byte_changes": byte_changes,
        "native_frame": frame_report(frame),
        "user_report": "User replied done to the fixed-Step5 Sound3 keyboard-key2 replacement protocol and supplied this capture; no deviation reported.",
        "limits": [
            "This supports keyboard indices0/1 for melodic keys1/2 on Sound3; other keys and sounds remain untested.",
            "The upper auxiliary nibble and primary note parameter bitfields remain opaque.",
            "This is a physical note control, not hardware acceptance of a generated key edit.",
        ],
    }
    output = root / "experiments/melodic-key2-results-001.json"
    validate_outputs([output], [registration_path, base_path, artifact_path, capture], False)
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Key2 control preservation/locality checks failed; results retained")


if __name__ == "__main__":
    main()
