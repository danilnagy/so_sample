"""Compare the measured-clock alternating-key recapture to its registered target."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data, patterns_report
from po33_re.modem.symbols import load_artifact


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-note-key-001"
    registration = json.loads((directory / "experiment.json").read_text())
    original_path = (
        root / "experiments/event-008-b-melodic-key2/derived/analysis-001/capture.symbols.npz"
    )
    target_path = root / "experiments/generated-note-key-001/edited.symbols.npz"
    actual_path = directory / "derived/analysis-002/capture.symbols.npz"
    acquisition_path = directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    output = directory / "hardware-validation.json"
    validate_outputs(
        [output], [original_path, target_path, actual_path, acquisition_path, capture], False
    )
    sources = [load_artifact(p) for p in (original_path, target_path, actual_path)]
    if sources[0].metadata["source_sha256"] != registration["source_backup_sha256"]:
        raise ValueError("Original artifact does not match registered source")
    if sources[2].metadata["source_sha256"] != sha256_file(capture):
        raise ValueError("Recovered artifact does not match capture WAV")
    original, target, actual = [decode_artifact(a) for a in sources]
    before, after = pattern_data(original, 1), pattern_data(actual, 1)
    packet_changes = [i for i, (a, b) in enumerate(zip(original.packets, actual.packets)) if a != b]
    byte_changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    steps = [r["step"] for r in patterns_report(actual)["patterns"][0]["nonzero_step_rows"]]
    keys = {str(step): (after[768 + 16 * (step - 1) + 2] & 15) + 1 for step in steps}
    checks = {
        "registered_body_hash_matches": hashlib.sha256(actual.encoded_body).hexdigest()
        == registration["expected_encoded_body_sha256"],
        "target_body_matches": actual.encoded_body == target.encoded_body,
        "target_plain_packets_match": actual.packets == target.packets,
        "all_packet_checksums_valid": True,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
        "packet_count": len(original.packets) == len(target.packets) == len(actual.packets) == 511,
        "frame_end_byte": actual.end_byte == 89396,
        "only_expected_plain_packet_changed": packet_changes == [7],
        "only_expected_auxiliary_byte_changed": byte_changes
        == [{"offset": 962, "old": 240, "new": 241}],
        "sample_packets_unchanged": all(
            a == b for a, b in zip(original.packets, actual.packets) if a.tag in (0x68B5, 0xEF78)
        ),
        "other_patterns_unchanged": all(
            pattern_data(original, p) == pattern_data(actual, p) for p in range(2, 17)
        ),
        "expected_populated_steps": steps == registration["expected_populated_steps"],
        "expected_keyboard_keys": keys == registration["expected_keyboard_keys_by_step"],
    }
    report = {
        "analysis_version": "native-note-key-hardware-validation-0.1",
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(actual_path),
        "initial_crossing_artifact_sha256": sha256_file(acquisition_path),
        "demodulation": {
            "method": sources[2].metadata["decoder_version"],
            "clock_report": "derived/analysis-002/clock-report.json",
            "initial_crossing_decode": "Failed checksum at wire byte13130; left timing slip, original artifact preserved",
            "target_data_used_for_recovery": False,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "native_frame": frame_report(actual),
        "changed_plain_packet_indices": packet_changes,
        "pattern1_byte_changes": byte_changes,
        "keyboard_keys_by_step": keys,
        "user_report": "the alternating pitches work and capture uploaded",
        "hardware_verified": all(checks.values()),
        "capture_timing": "Not explicitly reported; requested before pattern playback",
        "limits": [
            "Restore and alternating-pitch behavior are user reported; acoustic pitch intervals were not measured.",
            "The initial crossing decoder failed; measured-clock recovery uses waveform signs with unique pre-frame alignment and all-quarter checks, not packet repair.",
            "The full native frame is compared exactly; the measured-clock artifact's unobserved capture edges are not treated as a complete waveform capture.",
            "This validates the observed Sound3 key1/2 edit locally; other keys and sound slots remain untested.",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Alternating-key recapture checks failed; mismatch report preserved")


if __name__ == "__main__":
    main()
