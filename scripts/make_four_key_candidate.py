"""Build a four-note phrase using only physically calibrated keyboard values."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, rebuild_labels
from po33_re.formats.patterns import pattern_data, patterns_report, set_melodic_key
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact


def run(source_path, directory):
    root = Path(__file__).resolve().parents[1]
    validation_path = root / "experiments/melodic-key7-results-001.json"
    validation = json.loads(validation_path.read_text())
    source = load_artifact(source_path)
    if not validation["control_passed"] or not validation["all_registered_hypotheses_fit"]:
        raise ValueError("Middle-key invariants and hypotheses must both pass")
    if sha256_file(source_path) != validation["artifact_sha256"]:
        raise ValueError("Source must match the reviewed middle-key control")
    original = decode_artifact(source)
    endpoint_path = (
        root / "experiments/event-009-b-melodic-key16/derived/analysis-002/capture.symbols.npz"
    )
    endpoint = decode_artifact(load_artifact(endpoint_path))
    if encode_packets(set_melodic_key(endpoint, 1, 5, 3, 7)) != original.encoded_body:
        raise ValueError("Writer does not reproduce the genuine middle-key capture")
    if encode_packets(set_melodic_key(original, 1, 5, 3, 16)) != endpoint.encoded_body:
        raise ValueError("Writer does not reproduce the genuine endpoint inverse")
    unchanged_source = source.to_bytes()
    desired = {1: 1, 5: 2, 9: 7, 13: 16}
    working = source
    for step, key in desired.items():
        frame = decode_artifact(working)
        working = rebuild_labels(source, set_melodic_key(frame, 1, step, 3, key))
    working.metadata["transformations"].append(
        {
            "kind": "four-calibrated-key-phrase",
            "pattern_slot": 1,
            "sound_slot": 3,
            "keyboard_keys_by_step": {str(s): k for s, k in desired.items()},
            "source_artifact_sha256": sha256_file(source_path),
            "hardware_verified": False,
        }
    )
    target = decode_artifact(working)
    before, after = pattern_data(original, 1), pattern_data(target, 1)
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    expected_changes = [
        {"offset": 834, "old": 246, "new": 241},
        {"offset": 898, "old": 240, "new": 246},
        {"offset": 962, "old": 241, "new": 255},
    ]
    packet_changes = [i for i, (a, b) in enumerate(zip(original.packets, target.packets)) if a != b]
    checks = {
        "genuine_middle_and_endpoint_bodies_reproduced": True,
        "only_expected_auxiliary_bytes_changed": changes == expected_changes,
        "only_expected_plain_packet_changed": packet_changes == [7],
        "primary_note_data_unchanged": before[:768] == after[:768],
        "upper_nibbles_unchanged": all(
            a >> 4 == b >> 4 for a, b in zip(before[768:1024], after[768:1024])
        ),
        "packet_count_unchanged": len(original.packets) == len(target.packets) == 511,
        "packet_tags_and_lengths_unchanged": all(
            a.tag == b.tag and len(a.payload) == len(b.payload)
            for a, b in zip(original.packets, target.packets)
        ),
        "source_artifact_preserved": source.to_bytes() == unchanged_source,
    }
    paths = {
        name: directory / name
        for name in (
            "edited.symbols.npz",
            "restore-four-calibrated-keys.wav",
            "redecoded.symbols.npz",
            "pattern-report.json",
            "software-validation.json",
        )
    }
    validate_outputs(list(paths.values()), [source_path, endpoint_path, validation_path], False)
    write_bytes(paths["edited.symbols.npz"], working.to_bytes())
    waveform, encoding = encode_artifact(working, rate=44100, amplitude=0.5)
    write_bytes(paths["restore-four-calibrated-keys.wav"], waveform)
    redecoded = decode_wav(paths["restore-four-calibrated-keys.wav"], 0.02)
    write_bytes(paths["redecoded.symbols.npz"], redecoded.to_bytes())
    comparison = compare_artifacts(working, redecoded)
    recovered = decode_artifact(redecoded)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        exact_target_packets_after_wav_decode=recovered.packets == target.packets,
        exact_target_body_after_wav_decode=recovered.encoded_body == target.encoded_body,
    )
    write_bytes(paths["pattern-report.json"], json_bytes(patterns_report(target)))
    report = {
        "analysis_version": "four-calibrated-key-candidate-0.1",
        "source_capture_sha256": source.metadata["source_sha256"],
        "source_artifact_sha256": sha256_file(source_path),
        "restore_wav_sha256": sha256_file(paths["restore-four-calibrated-keys.wav"]),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_populated_steps": [1, 5, 9, 13],
        "expected_keyboard_keys_by_step": {str(s): k for s, k in desired.items()},
        "pattern1_byte_changes": changes,
        "changed_plain_packet_indices": packet_changes,
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "packets_after_wav_decode": frame_report(recovered),
        "hardware_verified": False,
        "limits": [
            "Only physically observed keys1/2/7/16 on Sound3 with primary0df883 are written; other keys remain unsupported.",
            "The auxiliary upper nibble and other note parameters are preserved and remain opaque.",
            "Keys7/16 have physical calibration evidence; this generated phrase needs its own musical and recapture validation.",
        ],
    }
    write_bytes(paths["software-validation.json"], json_bytes(report))
    if not report["passed"]:
        raise ValueError("Four-key candidate validation failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.out_dir.is_symlink():
        raise ValueError("Output directory cannot be a symbolic link")
    args.out_dir.mkdir(exist_ok=True)
    run(args.source, args.out_dir)


if __name__ == "__main__":
    main()
