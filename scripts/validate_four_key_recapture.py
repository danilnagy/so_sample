"""Compare the genuine four-calibrated-key recapture to its registered target."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data, patterns_report
from po33_re.modem.symbols import load_artifact


def comparison_checks(original, target, actual, registration):
    pattern = registration["expected_pattern"]
    sound = registration["expected_sound_slot"]
    before, after = pattern_data(original, pattern), pattern_data(actual, pattern)
    packet_changes = [i for i, (a, b) in enumerate(zip(original.packets, actual.packets)) if a != b]
    byte_changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    rows = patterns_report(actual)["patterns"][pattern - 1]["nonzero_step_rows"]
    steps = [row["step"] for row in rows]
    keys = {str(step): (after[768 + 16 * (step - 1) + sound - 1] & 15) + 1 for step in steps}
    checks = {
        "registered_body_hash_matches": hashlib.sha256(actual.encoded_body).hexdigest()
        == registration["expected_encoded_body_sha256"],
        "target_body_matches": actual.encoded_body == target.encoded_body,
        "target_plain_packets_match": actual.packets == target.packets,
        "all_packet_checksums_valid": True,  # Frames have already passed strict decoding.
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
        "packet_count": len(original.packets)
        == len(target.packets)
        == len(actual.packets)
        == registration["expected_packet_count"],
        "frame_end_byte": actual.end_byte == registration["expected_frame_end_byte"],
        "only_expected_plain_packets_changed": packet_changes
        == registration["expected_changed_plain_packet_indices"],
        "only_expected_pattern_bytes_changed": byte_changes
        == registration["expected_pattern_byte_changes"],
        "sample_packets_unchanged": all(
            a == b for a, b in zip(original.packets, actual.packets) if a.tag in (0x68B5, 0xEF78)
        ),
        "other_patterns_unchanged": all(
            pattern_data(original, p) == pattern_data(actual, p)
            for p in range(1, 17)
            if p != pattern
        ),
        "primary_note_fields_unchanged": before[:768] == after[:768],
        "auxiliary_upper_nibbles_unchanged": all(
            a >> 4 == b >> 4 for a, b in zip(before[768:1024], after[768:1024])
        ),
        "expected_populated_steps": steps == registration["expected_populated_steps"],
        "expected_keyboard_keys": keys == registration["expected_keyboard_keys_by_step"],
        "one_expected_sound_cell_per_step": all(
            [cell["cell_index"] for cell in row["nonzero_three_byte_cells"]] == [sound - 1]
            for row in rows
        ),
    }
    return checks, packet_changes, byte_changes, keys


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-four-keys-001"
    registration_path = directory / "restore-registration.json"
    registration = json.loads(registration_path.read_text())
    original_path = (
        root / "experiments/event-010-b-melodic-key7/derived/analysis-001/capture.symbols.npz"
    )
    target_path = root / "experiments/generated-four-keys-001/edited.symbols.npz"
    restore_path = root / "experiments/generated-four-keys-001/restore-four-calibrated-keys.wav"
    actual_path = directory / "derived/analysis-002/capture.symbols.npz"
    acquisition_path = directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    output = directory / "hardware-validation.json"
    validate_outputs(
        [output],
        [registration_path, original_path, target_path, restore_path, actual_path, capture],
        False,
    )
    sources = [load_artifact(p) for p in (original_path, target_path, actual_path)]
    if sources[0].metadata["source_sha256"] != registration["source_backup_sha256"]:
        raise ValueError("Original artifact does not match registered source")
    if sources[2].metadata["source_sha256"] != sha256_file(capture):
        raise ValueError("Recovered artifact does not match capture WAV")
    if sha256_file(restore_path) != registration["restore_wav_sha256"]:
        raise ValueError("Restore WAV does not match registration")
    original, target, actual = [decode_artifact(a) for a in sources]
    checks, packet_changes, byte_changes, keys = comparison_checks(
        original, target, actual, registration
    )
    report = {
        "analysis_version": "native-four-calibrated-keys-hardware-validation-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(actual_path),
        "initial_crossing_artifact_sha256": sha256_file(acquisition_path),
        "demodulation": {
            "method": sources[2].metadata["decoder_version"],
            "clock_report": "derived/analysis-002/clock-report.json",
            "initial_crossing_decode": "Checksum failure at wire byte9941, tag0xc498; original artifact retained",
            "target_data_used_for_recovery": False,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "native_frame": frame_report(actual),
        "changed_plain_packet_indices": packet_changes,
        "pattern1_byte_changes": byte_changes,
        "keyboard_keys_by_step": keys,
        "user_report": "done and confirmed matched",
        "manual_pitch_reference": "User confirms Pattern1 matched the auditioned Sound3 keys1/2/7/16 in order",
        "hardware_verified": all(checks.values()),
        "capture_timing": "Requested before audition and playback; user reports protocol completion without deviation",
        "limits": [
            "Musical behavior is user reported; acoustic frequencies and intervals were not measured.",
            "Only Sound3 keys1/2/7/16 with primary0df883 are validated; other keys, sounds and note parameters remain unsupported.",
            "Measured-clock recovery uses waveform signs and pre-frame alignment, not target bytes or checksum repair.",
            "The complete native frame matches exactly; unobserved waveform edges remain explicit in the recovered artifact.",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Four-calibrated-key recapture checks failed; report preserved")


if __name__ == "__main__":
    main()
