"""Remove Sound2 at Step1, preserving its Step9 copy and every Sound3 note."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, rebuild_labels
from po33_re.formats.patterns import (
    clone_sound_cell,
    pattern_data,
    patterns_report,
    remove_sound_cell,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact


def run(source_path, directory):
    root = Path(__file__).resolve().parents[1]
    validation_path = root / "experiments/edited-sound2-cell-001/hardware-validation.json"
    validation = json.loads(validation_path.read_text())
    if not validation["passed"] or not validation["hardware_verified"]:
        raise ValueError("Cell-copy hardware recapture must pass before the next candidate")
    if sha256_file(source_path) != validation["artifact_sha256"]:
        raise ValueError("Source must match the reviewed cell-copy recapture")
    source = load_artifact(source_path)
    unchanged = source.to_bytes()
    original = decode_artifact(source)
    control_path = (
        root / "experiments/event-011-b-sound2-layer/derived/analysis-001/capture.symbols.npz"
    )
    baseline_path = (
        root / "experiments/edited-four-keys-001/derived/analysis-002/capture.symbols.npz"
    )
    control, baseline = [decode_artifact(load_artifact(p)) for p in (control_path, baseline_path)]
    if encode_packets(remove_sound_cell(original, 1, 2, [9])) != control.encoded_body:
        raise ValueError("Removing Step9 does not reproduce the genuine one-cell control")
    if encode_packets(remove_sound_cell(control, 1, 2, [1])) != baseline.encoded_body:
        raise ValueError(
            "Removing the physical note does not reproduce the genuine four-key baseline"
        )
    if encode_packets(remove_sound_cell(original, 1, 2, [1, 9])) != baseline.encoded_body:
        raise ValueError("Removing both notes does not reproduce the genuine four-key baseline")
    packets = remove_sound_cell(original, 1, 2, [1])
    edited = rebuild_labels(source, packets)
    operation = {
        "kind": "observed-sound-cell-removal",
        "pattern_slot": 1,
        "sound_slot": 2,
        "steps": [1],
        "source_artifact_sha256": sha256_file(source_path),
        "hardware_verified": False,
    }
    edited.metadata["transformations"].append(operation)
    target = decode_artifact(edited)
    before, after = pattern_data(original, 1), pattern_data(target, 1)
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packet_changes = [i for i, (a, b) in enumerate(zip(original.packets, target.packets)) if a != b]
    checks = {
        "genuine_inverse_bodies_reproduced": True,
        "copy_from_remaining_step9_recreates_complete_source": encode_packets(
            clone_sound_cell(target, 1, 2, 9, [1])
        )
        == original.encoded_body,
        "only_expected_cell_bytes_cleared": changes
        == [
            {"offset": 3, "old": 13, "new": 0},
            {"offset": 4, "old": 40, "new": 0},
            {"offset": 5, "old": 49, "new": 0},
            {"offset": 769, "old": 240, "new": 0},
        ],
        "only_expected_plain_packets_changed": packet_changes == [4, 7],
        "all_sound3_cells_unchanged": all(
            before[48 * s + 6 : 48 * s + 9] == after[48 * s + 6 : 48 * s + 9]
            and before[768 + 16 * s + 2] == after[768 + 16 * s + 2]
            for s in range(16)
        ),
        "remaining_sound2_step9_unchanged": before[387:390] == after[387:390]
        and before[897] == after[897],
        "samples_unchanged": all(
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
        "restore-remove-sound2-step1.wav",
        "redecoded.symbols.npz",
        "pattern-report.json",
        "software-validation.json",
    ]
    paths = {name: directory / name for name in names}
    validate_outputs(
        list(paths.values()), [source_path, validation_path, control_path, baseline_path], False
    )
    write_bytes(paths["edited.symbols.npz"], edited.to_bytes())
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    write_bytes(paths["restore-remove-sound2-step1.wav"], waveform)
    redecoded = decode_wav(paths["restore-remove-sound2-step1.wav"], 0.02)
    write_bytes(paths["redecoded.symbols.npz"], redecoded.to_bytes())
    comparison = compare_artifacts(edited, redecoded)
    recovered = decode_artifact(redecoded)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        exact_target_body_after_wav_decode=recovered.encoded_body == target.encoded_body,
        exact_target_packets_after_wav_decode=recovered.packets == target.packets,
    )
    write_bytes(paths["pattern-report.json"], json_bytes(patterns_report(target)))
    report = {
        "analysis_version": "sound2-cell-removal-candidate-0.1",
        "source_capture_sha256": source.metadata["source_sha256"],
        "source_artifact_sha256": sha256_file(source_path),
        "restore_wav_sha256": sha256_file(paths["restore-remove-sound2-step1.wav"]),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound2_steps": [9],
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
            "Only occupied, observed Sound2 primary0d2831/F0 cells and optional calibrated Sound3 neighbours are supported",
            "Existing genuine inverse bodies are reproduced exactly; this new Step1 removal needs its own hardware validation",
            "Primary note parameters remain opaque; no other sound deletion or Sound2 pitch edit is enabled",
        ],
    }
    write_bytes(paths["software-validation.json"], json_bytes(report))
    if not report["passed"]:
        raise ValueError("Sound2 removal candidate software validation failed")


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
