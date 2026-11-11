"""Copy the observed Sound2 cell to Step9 while retaining every Sound3 note."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report, rebuild_labels
from po33_re.formats.patterns import clone_sound_cell, pattern_data, patterns_report
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact


def run(source_path, directory):
    root = Path(__file__).resolve().parents[1]
    validation_path = root / "experiments/sound2-layer-results-001.json"
    validation = json.loads(validation_path.read_text())
    source = load_artifact(source_path)
    if not validation["control_passed"]:
        raise ValueError("Physical addition preservation checks must pass")
    if sha256_file(source_path) != validation["artifact_sha256"]:
        raise ValueError("Source must match the reviewed Sound2 control")
    original = decode_artifact(source)
    before = pattern_data(original, 1)
    if before[3:6] != bytes.fromhex("0d2831") or before[769] != 240:
        raise ValueError("Source must contain the actual observed Sound2 note parameters")
    unchanged = source.to_bytes()
    packets = clone_sound_cell(original, 1, 2, 1, [9])
    edited = rebuild_labels(source, packets)
    operation = {
        "kind": "opaque-sound-cell-clone",
        "pattern_slot": 1,
        "sound_slot": 2,
        "source_step": 1,
        "target_steps": [9],
        "source_artifact_sha256": sha256_file(source_path),
        "primary_hex": "0d2831",
        "auxiliary_byte": 240,
        "hardware_verified": False,
    }
    edited.metadata["transformations"].append(operation)
    target = decode_artifact(edited)
    after = pattern_data(target, 1)
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packet_changes = [i for i, (a, b) in enumerate(zip(original.packets, target.packets)) if a != b]
    checks = {
        "only_expected_cell_bytes_changed": changes
        == [
            {"offset": 387, "old": 0, "new": 13},
            {"offset": 388, "old": 0, "new": 40},
            {"offset": 389, "old": 0, "new": 49},
            {"offset": 897, "old": 0, "new": 240},
        ],
        "only_expected_plain_packets_changed": packet_changes == [5, 7],
        "all_sound3_cells_unchanged": all(
            before[48 * s + 6 : 48 * s + 9] == after[48 * s + 6 : 48 * s + 9]
            and before[768 + 16 * s + 2] == after[768 + 16 * s + 2]
            for s in range(16)
        ),
        "source_sound2_cell_preserved": before[3:6] == after[3:6] and before[769] == after[769],
        "sample_packets_unchanged": all(
            a == b for a, b in zip(original.packets, target.packets) if a.tag in (0x68B5, 0xEF78)
        ),
        "other_patterns_unchanged": all(
            pattern_data(original, p) == pattern_data(target, p) for p in range(2, 17)
        ),
        "packet_count": len(original.packets) == len(target.packets) == 511,
        "packet_tags_and_lengths": all(
            a.tag == b.tag and len(a.payload) == len(b.payload)
            for a, b in zip(original.packets, target.packets)
        ),
        "source_artifact_preserved": source.to_bytes() == unchanged,
    }
    names = [
        "edited.symbols.npz",
        "restore-sound2-step9.wav",
        "redecoded.symbols.npz",
        "pattern-report.json",
        "software-validation.json",
    ]
    paths = {name: directory / name for name in names}
    validate_outputs(list(paths.values()), [source_path, validation_path], False)
    write_bytes(paths["edited.symbols.npz"], edited.to_bytes())
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    write_bytes(paths["restore-sound2-step9.wav"], waveform)
    redecoded = decode_wav(paths["restore-sound2-step9.wav"], 0.02)
    write_bytes(paths["redecoded.symbols.npz"], redecoded.to_bytes())
    comparison = compare_artifacts(edited, redecoded)
    recovered = decode_artifact(redecoded)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        exact_target_packets_after_wav_decode=recovered.packets == target.packets,
        exact_target_body_after_wav_decode=recovered.encoded_body == target.encoded_body,
    )
    write_bytes(paths["pattern-report.json"], json_bytes(patterns_report(target)))
    report = {
        "analysis_version": "sound2-cell-clone-candidate-0.1",
        "source_capture_sha256": source.metadata["source_sha256"],
        "source_artifact_sha256": sha256_file(source_path),
        "restore_wav_sha256": sha256_file(paths["restore-sound2-step9.wav"]),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound2_steps": [1, 9],
        "expected_sound3_keys_by_step": {"1": 1, "5": 2, "9": 7, "13": 16},
        "pattern1_byte_changes": changes,
        "changed_plain_packet_indices": packet_changes,
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "packets_after_wav_decode": frame_report(recovered),
        "hardware_verified": False,
        "limits": [
            "The Sound2 primary-equality hypothesis failed; this copies its actual0d2831/F0 cell intact.",
            "Only this observed Sound2 cell with optional calibrated Sound3 neighbours is supported.",
            "Note parameters remain opaque; no Sound2 key editor or general polyphony behavior is claimed.",
            "Generated cell-copy acceptance needs its own hardware restore and recapture.",
        ],
    }
    write_bytes(paths["software-validation.json"], json_bytes(report))
    if not report["passed"]:
        raise ValueError("Sound2 cell-copy software validation failed")


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
