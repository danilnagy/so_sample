"""Build an alternating key1/key2 pattern with one calibrated auxiliary-byte edit."""

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
    validation_path = root / "experiments/melodic-key2-results-001.json"
    validation = json.loads(validation_path.read_text())
    source = load_artifact(source_path)
    if not validation["control_passed"] or not validation["all_registered_hypotheses_fit"]:
        raise ValueError("Key control invariants and registered hypotheses must both pass")
    if sha256_file(source_path) != validation["artifact_sha256"]:
        raise ValueError("Source must match the reviewed key2 control artifact")
    original = decode_artifact(source)
    base_path = root / "experiments/edited-pattern-001/derived/analysis-001/capture.symbols.npz"
    base = decode_artifact(load_artifact(base_path))
    if encode_packets(set_melodic_key(base, 1, 5, 3, 2)) != original.encoded_body:
        raise ValueError("Key writer does not reproduce the genuine key2 capture")
    if encode_packets(set_melodic_key(original, 1, 5, 3, 1)) != base.encoded_body:
        raise ValueError("Key writer does not restore the genuine key1 baseline body")
    unchanged_source = source.to_bytes()
    packets = set_melodic_key(original, 1, 13, 3, 2)
    artifact = rebuild_labels(source, packets)
    artifact.metadata["transformations"].append(
        {
            "kind": "calibrated-melodic-key-edit",
            "pattern_slot": 1,
            "step": 13,
            "sound_slot": 3,
            "keyboard_key": 2,
            "source_artifact_sha256": sha256_file(source_path),
            "hardware_verified": False,
        }
    )
    target = decode_artifact(artifact)
    before, after = pattern_data(original, 1), pattern_data(target, 1)
    byte_changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packet_changes = [i for i, (a, b) in enumerate(zip(original.packets, packets)) if a != b]
    checks = {
        "genuine_key2_body_reproduced": True,
        "genuine_key1_body_reproduced_by_inverse": True,
        "only_registered_auxiliary_byte_changed": byte_changes
        == [{"offset": 962, "old": 240, "new": 241}],
        "only_registered_plain_packet_changed": packet_changes == [7],
        "packet_count_unchanged": len(original.packets) == len(packets) == 511,
        "packet_tags_and_lengths_unchanged": all(
            a.tag == b.tag and len(a.payload) == len(b.payload)
            for a, b in zip(original.packets, packets)
        ),
        "primary_note_data_unchanged": before[:768] == after[:768],
        "upper_nibbles_unchanged": all(
            a >> 4 == b >> 4 for a, b in zip(before[768:1024], after[768:1024])
        ),
        "source_artifact_preserved": source.to_bytes() == unchanged_source,
    }
    paths = {
        name: directory / name
        for name in (
            "edited.symbols.npz",
            "restore-alternating-keys.wav",
            "redecoded.symbols.npz",
            "pattern-report.json",
            "software-validation.json",
        )
    }
    validate_outputs(list(paths.values()), [source_path, base_path, validation_path], False)
    write_bytes(paths["edited.symbols.npz"], artifact.to_bytes())
    waveform, encoding = encode_artifact(artifact, rate=44100, amplitude=0.5)
    write_bytes(paths["restore-alternating-keys.wav"], waveform)
    redecoded = decode_wav(paths["restore-alternating-keys.wav"], 0.02)
    write_bytes(paths["redecoded.symbols.npz"], redecoded.to_bytes())
    comparison = compare_artifacts(artifact, redecoded)
    recovered = decode_artifact(redecoded)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        exact_target_packets_after_wav_decode=recovered.packets == packets,
        exact_target_body_after_wav_decode=recovered.encoded_body == target.encoded_body,
    )
    write_bytes(paths["pattern-report.json"], json_bytes(patterns_report(target)))
    report = {
        "analysis_version": "calibrated-note-key-candidate-0.1",
        "source_capture_sha256": source.metadata["source_sha256"],
        "source_artifact_sha256": sha256_file(source_path),
        "restore_wav_sha256": sha256_file(paths["restore-alternating-keys.wav"]),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "changed_plain_packet_indices": packet_changes,
        "pattern1_byte_changes": byte_changes,
        "expected_populated_steps": [1, 5, 9, 13],
        "expected_keyboard_keys_by_step": {"1": 1, "5": 2, "9": 1, "13": 2},
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "packets_after_wav_decode": frame_report(recovered),
        "hardware_verified": False,
        "limits": [
            "Only locally observed Sound3 keys1/2 with primary0df883 and auxiliaryF0/F1 are supported.",
            "The auxiliary upper nibble and primary bitfields remain opaque; no other note parameter is changed.",
            "Exact reproduction of a physical key control is software evidence; this generated key edit still needs hardware validation.",
        ],
    }
    write_bytes(paths["software-validation.json"], json_bytes(report))
    if not report["passed"]:
        raise ValueError("Generated key edit software checks failed")


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
