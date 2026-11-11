"""Validate the hardware recapture of the registered Sound3 trim candidate."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, sound_data
from po33_re.modem.symbols import load_artifact


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-trim-001"
    original_path = root / (
        "experiments/empty-001-h-sound3-copy-return/derived/analysis-001/capture.symbols.npz"
    )
    target_path = root / "experiments/generated-sound3-short-001/edited.symbols.npz"
    actual_path = directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    registration = json.loads((directory / "experiment.json").read_text())
    output = directory / "hardware-validation.json"
    validate_outputs([output], [original_path, target_path, actual_path, capture], False)
    original, target, actual = [
        decode_artifact(load_artifact(p)) for p in (original_path, target_path, actual_path)
    ]
    source_hash = sha256_file(capture)
    if load_artifact(actual_path).metadata["source_sha256"] != source_hash:
        raise ValueError("Recapture artifact does not match the source WAV")
    body_hash = hashlib.sha256(actual.encoded_body).hexdigest()
    counters = {
        str(slot): int.from_bytes(sound_data(actual, slot - 1)[4:8], "little")
        for slot in (1, 2, 3, 8)
    }
    changes = [i for i, (a, b) in enumerate(zip(original.packets, actual.packets)) if a != b]
    checks = {
        "registered_body_sha256_matches": body_hash == registration["expected_encoded_body_sha256"],
        "generated_body_matches_recapture": target.encoded_body == actual.encoded_body,
        "generated_plain_packets_match_recapture": target.packets == actual.packets,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
        "all_packet_checksums_valid": True,
        "packet_count_unchanged": len(original.packets)
        == len(target.packets)
        == len(actual.packets)
        == 511,
        "only_registered_trim_packet_changed": changes == [375],
        "expected_counters": counters == {"1": 64704, "2": 64704, "3": 8000, "8": 64704},
        "backing_sample_bytes_unchanged": sound_data(original, 0)[9:] == sound_data(actual, 0)[9:],
    }
    report = {
        "analysis_version": "native-trim-hardware-validation-0.1",
        "capture_sha256": source_hash,
        "recapture_artifact_sha256": sha256_file(actual_path),
        "generated_artifact_sha256": sha256_file(target_path),
        "encoded_body_sha256": body_hash,
        "packet_count": len(actual.packets),
        "frame_end_byte": actual.end_byte,
        "sound_counters": counters,
        "changed_plain_packet_indices": changes,
        "backing_sample_sha256": hashlib.sha256(sound_data(actual, 0)[9:]).hexdigest(),
        "checks": checks,
        "passed": all(checks.values()),
        "user_report": "Everything worked with upload and the tone test; recapture supplied.",
        "hardware_verified": all(checks.values()),
        "limits": [
            "Restore and audible behavior are user reported; buttons and playback were not observed independently.",
            "The complete checksum-validated body is compared; acquisition and post-frame carrier are separate.",
            "This validates this candidate and local device path, not arbitrary sample or pattern edits.",
            "The unedited generated control was not separately tested on hardware.",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Registered native trim recapture checks failed")


if __name__ == "__main__":
    main()
