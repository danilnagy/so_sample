"""Build the first four-note pattern restore from the recorded melodic step."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, rebuild_labels
from po33_re.formats.patterns import clone_step, pattern_data, pattern_groups, patterns_report
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact


def run(source_path, directory):
    root = Path(__file__).resolve().parents[1]
    validation_path = root / "experiments/melodic-step1-results-001.json"
    validation = json.loads(validation_path.read_text())
    source = load_artifact(source_path)
    if not validation["passed"] or sha256_file(source_path) != validation["artifact_sha256"]:
        raise ValueError("Source must match the validated single melodic event artifact")
    original = decode_artifact(source)
    if (
        hashlib.sha256(original.encoded_body).hexdigest()
        != validation["native_frame"]["encoded_body_sha256"]
    ):
        raise ValueError("Source native body does not match validated control")
    # Independent genuine corrected joint-state reconstruction guards the writer.
    first_path = root / "experiments/event-001-b/derived/analysis-001/capture.symbols.npz"
    joint_path = root / "experiments/event-005-b-joint/derived/analysis-002/capture.symbols.npz"
    first, joint = [decode_artifact(load_artifact(p)) for p in (first_path, joint_path)]
    if encode_packets(clone_step(first, 1, 1, (2,))) != joint.encoded_body:
        raise ValueError("Opaque-step cloning does not reproduce the genuine joint control")
    unchanged_source = source.to_bytes()
    packets = clone_step(original, 1, 1, (5, 9, 13))
    artifact = rebuild_labels(source, packets)
    artifact.metadata["transformations"].append(
        {
            "kind": "opaque-step-clone",
            "pattern_slot": 1,
            "source_step": 1,
            "target_steps": [5, 9, 13],
            "source_artifact_sha256": sha256_file(source_path),
            "hardware_verified": False,
        }
    )
    target = decode_artifact(artifact)
    changes = [i for i, (a, b) in enumerate(zip(original.packets, packets)) if a != b]
    allowed = set(pattern_groups(original)[0])
    before, after = pattern_data(original, 1), pattern_data(target, 1)
    expected = bytearray(before)
    for step in (5, 9, 13):
        p, a = 48 * (step - 1), 768 + 16 * (step - 1)
        expected[p : p + 48] = before[:48]
        expected[a : a + 16] = before[768:784]
    checks = {
        "known_joint_encoded_body_reproduced": True,
        "only_pattern1_data_packets_changed": bool(changes) and set(changes) <= allowed,
        "packet_count_unchanged": len(original.packets) == len(packets) == 511,
        "packet_tags_and_lengths_unchanged": all(
            a.tag == b.tag and len(a.payload) == len(b.payload)
            for a, b in zip(original.packets, packets)
        ),
        "expected_raw_rows_only": after == bytes(expected),
        "source_step_preserved": before[:48] == after[:48] and before[768:784] == after[768:784],
        "footer_preserved": before[1024:] == after[1024:],
        "other_patterns_preserved": all(
            pattern_data(original, p) == pattern_data(target, p) for p in range(2, 17)
        ),
        "source_artifact_preserved": source.to_bytes() == unchanged_source,
    }
    paths = {
        name: directory / name
        for name in (
            "edited.symbols.npz",
            "restore-four-notes.wav",
            "redecoded.symbols.npz",
            "pattern-report.json",
            "software-validation.json",
        )
    }
    validate_outputs(
        list(paths.values()), [source_path, validation_path, first_path, joint_path], False
    )
    write_bytes(paths["edited.symbols.npz"], artifact.to_bytes())
    waveform, encoding = encode_artifact(artifact, rate=44100, amplitude=0.5)
    write_bytes(paths["restore-four-notes.wav"], waveform)
    redecoded = decode_wav(paths["restore-four-notes.wav"], 0.02)
    write_bytes(paths["redecoded.symbols.npz"], redecoded.to_bytes())
    comparison = compare_artifacts(artifact, redecoded)
    recovered = decode_artifact(redecoded)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        exact_target_packets_after_wav_decode=recovered.packets == packets,
        exact_target_body_after_wav_decode=recovered.encoded_body == target.encoded_body,
    )
    pattern_report = patterns_report(target)
    write_bytes(paths["pattern-report.json"], json_bytes(pattern_report))
    report = {
        "analysis_version": "opaque-step-clone-candidate-0.1",
        "source_capture_sha256": source.metadata["source_sha256"],
        "source_artifact_sha256": sha256_file(source_path),
        "known_joint_source_sha256": load_artifact(joint_path).metadata["source_sha256"],
        "restore_wav_sha256": sha256_file(paths["restore-four-notes.wav"]),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "pattern_slot": 1,
        "source_step": 1,
        "added_steps": [5, 9, 13],
        "expected_populated_steps": [1, 5, 9, 13],
        "expected_source_primary_hex": before[:48].hex(),
        "expected_source_auxiliary_hex": before[768:784].hex(),
        "changed_plain_packet_indices": changes,
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "packets_after_wav_decode": frame_report(recovered),
        "hardware_verified": False,
        "limits": [
            "Raw primary and auxiliary rows are copied; sound/pitch/gate bitfields are not independently decoded.",
            "Targets must be fully empty and the source must contain exactly one primary/auxiliary cell.",
            "The Step2-only drum auxiliary discrepancy remains unresolved; it is not changed or generalized here.",
            "Software and genuine joint reconstruction do not establish hardware acceptance of this new pattern.",
        ],
    }
    write_bytes(paths["software-validation.json"], json_bytes(report))
    if not report["passed"]:
        raise ValueError("Pattern candidate software checks failed")


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
