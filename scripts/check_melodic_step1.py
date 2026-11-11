"""Evaluate the preregistered single melodic event against its verified baseline."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data, pattern_groups
from po33_re.modem.symbols import load_artifact


def main():
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments/melodic-step1-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    base_path = root / "experiments/edited-sample-001/derived/analysis-001/capture.symbols.npz"
    directory = root / "experiments/event-007-b-melodic"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    base_artifact, artifact = load_artifact(base_path), load_artifact(artifact_path)
    base, frame = decode_artifact(base_artifact), decode_artifact(artifact)
    if base_artifact.metadata["source_sha256"] != registration["baseline_source_sha256"]:
        raise ValueError("Baseline does not match registration")
    if hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]:
        raise ValueError("Baseline body does not match registration")
    if artifact.metadata["source_sha256"] != sha256_file(capture):
        raise ValueError("New artifact does not match capture WAV")
    a, b = pattern_data(base, 1), pattern_data(frame, 1)
    changes = [i for i, (x, y) in enumerate(zip(base.packets, frame.packets)) if x != y]
    allowed = set(pattern_groups(base)[0])
    checks = {
        "native_packets_and_crc": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
        "packet_count": len(base.packets) == len(frame.packets) == 511,
        "frame_end_byte": frame.end_byte == 89396,
        "sound_data": all(
            x == y for x, y in zip(base.packets, frame.packets) if x.tag in (0x68B5, 0xEF78)
        ),
        "other_patterns": all(
            pattern_data(base, p) == pattern_data(frame, p) for p in range(2, 17)
        ),
        "all_other_plain_packets": bool(changes) and set(changes) <= allowed,
        "pattern1_change": a[:48] != b[:48],
        "primary_locality": a[48:768] == b[48:768],
        "auxiliary_locality": a[784:1024] == b[784:1024],
        "footer": a[1024:] == b[1024:],
    }
    report = {
        "analysis_version": "native-melodic-step1-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "baseline_source_sha256": base_artifact.metadata["source_sha256"],
        "capture_sha256": artifact.metadata["source_sha256"],
        "artifact_sha256": sha256_file(artifact_path),
        "checks": checks,
        "passed": all(checks.values()),
        "changed_plain_packet_indices": changes,
        "pattern1_byte_changes": [
            {"offset": i, "old": x, "new": y} for i, (x, y) in enumerate(zip(a, b)) if x != y
        ],
        "step1_primary_hex": b[:48].hex(),
        "step1_auxiliary_hex": b[768:784].hex(),
        "native_frame": frame_report(frame),
        "user_report": "User replied done to the requested single melodic note protocol and supplied this capture; no deviation reported.",
        "hardware_pattern_edit_verified": False,
        "limits": [
            "This is a hardware-created note control, not a generated pattern restore.",
            "Exact key presses were not independently observed; raw fields are not decoded into pitch, volume or duration.",
        ],
    }
    output = root / "experiments/melodic-step1-results-001.json"
    validate_outputs([output], [registration_path, base_path, artifact_path, capture], False)
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Registered melodic step checks failed")


if __name__ == "__main__":
    main()
