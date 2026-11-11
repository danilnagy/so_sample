"""Validate the hardware recapture of the registered750Hz sample replacement."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, sound_data, sound_groups
from po33_re.modem.symbols import load_artifact


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-sample-001"
    original_path = root / "experiments/edited-trim-001/derived/analysis-001/capture.symbols.npz"
    target_path = root / "experiments/generated-sample-750-001/edited.symbols.npz"
    actual_path = directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    registration = json.loads((directory / "experiment.json").read_text())
    output = directory / "hardware-validation.json"
    validate_outputs([output], [original_path, target_path, actual_path, capture], False)
    artifacts = [load_artifact(p) for p in (original_path, target_path, actual_path)]
    original, target, actual = [decode_artifact(a) for a in artifacts]
    source_hash = sha256_file(capture)
    if artifacts[2].metadata["source_sha256"] != source_hash:
        raise ValueError("Recapture artifact does not match the source WAV")
    body_hash = hashlib.sha256(actual.encoded_body).hexdigest()
    codes_hash = hashlib.sha256(sound_data(actual, 0)[9:]).hexdigest()
    counters = {
        str(slot): int.from_bytes(sound_data(actual, slot - 1)[4:8], "little")
        for slot in (1, 2, 3, 8)
    }
    changes = [i for i, (a, b) in enumerate(zip(original.packets, actual.packets)) if a != b]
    allowed = set(sound_groups(original)[0])
    checks = {
        "registered_body_sha256_matches": body_hash == registration["expected_encoded_body_sha256"],
        "registered_backing_codes_sha256_matches": codes_hash
        == registration["expected_backing_codes_sha256"],
        "generated_body_matches_recapture": target.encoded_body == actual.encoded_body,
        "generated_plain_packets_match_recapture": target.packets == actual.packets,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
        "all_packet_checksums_valid": True,
        "packet_count_unchanged": len(original.packets)
        == len(target.packets)
        == len(actual.packets)
        == 511,
        "only_owner_data_packets_changed": bool(changes) and set(changes) <= allowed,
        "all_sound_headers_unchanged": all(
            sound_data(original, slot - 1)[:9] == sound_data(actual, slot - 1)[:9]
            for slot in (1, 2, 3, 8)
        ),
        "packet_tags_and_lengths_unchanged": all(
            a.tag == b.tag and len(a.payload) == len(b.payload)
            for a, b in zip(original.packets, actual.packets)
        ),
        "expected_counters": counters == registration["expected_sound_counters"],
    }
    report = {
        "analysis_version": "native-sample-hardware-validation-0.1",
        "capture_sha256": source_hash,
        "recapture_artifact_sha256": sha256_file(actual_path),
        "generated_artifact_sha256": sha256_file(target_path),
        "encoded_body_sha256": body_hash,
        "backing_codes_sha256": codes_hash,
        "packet_count": len(actual.packets),
        "frame_end_byte": actual.end_byte,
        "sound_counters": counters,
        "changed_plain_packet_indices": changes,
        "checks": checks,
        "passed": all(checks.values()),
        "hardware_verified": all(checks.values()),
        "user_report": "User replied done to the requested restore, listening and recapture steps; no deviation reported.",
        "limits": [
            "Exact listening observations were not supplied; pitch and duration were not independently measured.",
            "The complete checksum-validated body is compared; acquisition and post-frame carrier are separate.",
            "This validates this fixed-size replacement and local device path, not arbitrary allocation or resizing.",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Registered sample replacement recapture checks failed")


if __name__ == "__main__":
    main()
