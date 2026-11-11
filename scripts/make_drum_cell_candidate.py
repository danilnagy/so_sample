"""Compile a copy of the observed opaque Sound10 note from Step1 to Step9."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import clone_drum_cell, pattern_data, remove_drum_cell
from po33_re.modem.symbols import load_artifact


def run(plan_path, output_directory):
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-020-b-drum10-key1-step1"
    source_path = directory / "derived/analysis-001/capture.symbols.npz"
    evidence_path = root / "experiments/drum10-note-results-001.json"
    registration_path = root / "experiments/drum10-note-predictions-001.json"
    evidence, registration = [json.loads(p.read_text()) for p in (evidence_path, registration_path)]
    baseline_path = directory / registration["baseline_artifact"]
    capture = directory / "capture.wav"
    if (
        not evidence["control_passed"]
        or not evidence["hypothesis_checks"]["sound10_maps_to_cell10"]
        or evidence["observed_note"]["candidate_primary_hex"] != "0df883"
        or evidence["observed_note"]["candidate_auxiliary_byte"] != 0x10
        or sha256_file(registration_path) != evidence["registration_sha256"]
        or sha256_file(source_path) != evidence["artifact_sha256"]
        or sha256_file(capture) != evidence["capture_sha256"]
        or sha256_file(baseline_path) != registration["baseline_artifact_sha256"]
    ):
        raise ValueError("Matching reviewed drum-note evidence and raw0df883/10 cell required")
    source = load_artifact(source_path)
    original, baseline = decode_artifact(source), decode_artifact(load_artifact(baseline_path))
    if (
        source.metadata["source_sha256"] != evidence["capture_sha256"]
        or hashlib.sha256(original.encoded_body).hexdigest()
        != evidence["native_frame"]["encoded_body_sha256"]
        or hashlib.sha256(baseline.encoded_body).hexdigest() != registration["baseline_body_sha256"]
    ):
        raise ValueError("Source/baseline native bodies differ from reviewed identities")
    expected_operation = {
        "operation": "clone_drum_cell",
        "pattern": 1,
        "sound": 10,
        "source_step": 1,
        "target_steps": [9],
    }
    if json.loads(plan_path.read_text()).get("operations") != [expected_operation]:
        raise ValueError("This experiment requires exactly the Sound10 Step1 to Step9 copy")
    checks = {
        "genuine_before_addition_body_reproduced": encode_packets(
            remove_drum_cell(original, 1, 10, [1])
        )
        == baseline.encoded_body,
    }
    if not all(checks.values()):
        raise ValueError("Bounded removal does not reproduce the complete genuine baseline")
    compiled = compile_edit_plan(source_path, plan_path, output_directory)
    target = decode_artifact(load_artifact(output_directory / "edited.symbols.npz"))
    before, after = pattern_data(original, 1), pattern_data(target, 1)
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packet_changes = [i for i, (a, b) in enumerate(zip(original.packets, target.packets)) if a != b]
    expected_changes = [
        {"offset": 411, "old": 0, "new": 13},
        {"offset": 412, "old": 0, "new": 248},
        {"offset": 413, "old": 0, "new": 131},
        {"offset": 905, "old": 0, "new": 16},
    ]
    only9 = decode_frame(bytes(4095) + encode_packets(remove_drum_cell(target, 1, 10, [1])))
    both = decode_frame(bytes(4095) + encode_packets(clone_drum_cell(only9, 1, 10, 9, [1])))
    recovered = encode_packets(remove_drum_cell(both, 1, 10, [9]))
    checks.update(
        exact_expected_step9_cell_bytes=changes == expected_changes,
        only_expected_plain_packets_changed=packet_changes == [5, 7],
        entire_genuine_addition_body_reproduced=recovered == original.encoded_body,
        candidate_inverse_reproduces_source=encode_packets(remove_drum_cell(target, 1, 10, [9]))
        == original.encoded_body,
        both_drumnotes_removed_reproduce_genuine_baseline=encode_packets(
            remove_drum_cell(target, 1, 10, [1, 9])
        )
        == baseline.encoded_body,
        all_compiler_roundtrip_checks=compiled["passed"] and all(compiled["checks"].values()),
        source_artifact_preserved=sha256_file(source_path) == evidence["artifact_sha256"],
        source_capture_preserved=sha256_file(capture) == evidence["capture_sha256"],
    )
    report = {
        "analysis_version": "first-drum-cell-copy-candidate-0.1",
        "control_evidence_sha256": sha256_file(evidence_path),
        "source_capture_sha256": evidence["capture_sha256"],
        "source_artifact_sha256": evidence["artifact_sha256"],
        "source_body_sha256": evidence["native_frame"]["encoded_body_sha256"],
        "restore_wav_sha256": compiled["restore_wav_sha256"],
        "expected_body_sha256": compiled["target_body_sha256"],
        "pattern": 1,
        "sound": 10,
        "source_step": 1,
        "target_steps": [9],
        "primary_hex": "0df883",
        "auxiliary_byte": 16,
        "pattern1_byte_changes": changes,
        "changed_plain_packet_indices": packet_changes,
        "checks": checks,
        "passed": all(checks.values()),
        "hardware_verified": False,
        "compiler_report": "compile-report.json",
        "limits": [
            "Only the observed opaque Sound10/key1 primary0df883/auxiliary10 cell is copied; no drum-key or parameter encoding is inferred",
            "Pattern1, accepted copied Sound10 window and calibrated Sound2/Sound3 neighbors bound the writers",
            "Source note, all other cells/patterns, samples/references and opaque packets remain intact; occupied targets are rejected",
            "This generated three-sound Step9 combination needs its own hardware restore and recapture",
            "The failed F0 auxiliary prediction is retained independently; it is never substituted into the copied cell",
        ],
    }
    write_bytes(output_directory / "software-validation.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Drum-cell copy software checks failed; outputs retained")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.plan, args.out_dir)


if __name__ == "__main__":
    main()
