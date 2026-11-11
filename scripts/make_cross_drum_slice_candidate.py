"""Compile a narrowly guarded Sound9/key2 to Sound10/key1 reference-copy candidate."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.drums import copy_calibrated_drum_slice, replace_calibrated_drum_slice_end
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets, sound_data
from po33_re.modem.symbols import load_artifact


def reframed(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


def run(plan_path, output_directory):
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-019-b-copy-drum9-key1-to-drum10-key1"
    evidence_path = root / "experiments/cross-drum-slice-copy-results-001.json"
    registration_path = root / "experiments/cross-drum-slice-copy-predictions-001.json"
    evidence, registration = [json.loads(p.read_text()) for p in (evidence_path, registration_path)]
    source_path = directory / "derived/analysis-001/capture.symbols.npz"
    baseline_path = directory / registration["baseline_artifact"]
    capture = directory / "capture.wav"
    if (
        not evidence["control_passed"]
        or not all(evidence["hypothesis_checks"].values())
        or sha256_file(registration_path) != evidence["registration_sha256"]
        or sha256_file(source_path) != evidence["artifact_sha256"]
        or sha256_file(capture) != evidence["capture_sha256"]
        or sha256_file(baseline_path) != registration["baseline_artifact_sha256"]
    ):
        raise ValueError("Matching reviewed physical cross-drum copy evidence required")
    source = load_artifact(source_path)
    copied, baseline = decode_artifact(source), decode_artifact(load_artifact(baseline_path))
    if (
        source.metadata["source_sha256"] != evidence["capture_sha256"]
        or hashlib.sha256(copied.encoded_body).hexdigest()
        != evidence["native_frame"]["encoded_body_sha256"]
        or hashlib.sha256(baseline.encoded_body).hexdigest() != registration["baseline_body_sha256"]
    ):
        raise ValueError("Source/baseline bodies differ from reviewed identities")
    operation = {
        "operation": "copy_drum_slice",
        "source_sound": 9,
        "source_slice": 2,
        "destination_sound": 10,
        "destination_slice": 1,
    }
    if json.loads(plan_path.read_text()).get("operations") != [operation]:
        raise ValueError("This experiment requires exactly Sound9/key2 to Sound10/key1")
    # Reverse the observed key1 copy through bounded source edits, retaining the
    # source's accepted2000 endpoint after copying its original4044 reference.
    inverse = reframed(replace_calibrated_drum_slice_end(copied, 9, 1, 4044))
    inverse = reframed(copy_calibrated_drum_slice(inverse, 9, 1, 10, 1))
    inverse = reframed(replace_calibrated_drum_slice_end(inverse, 9, 1, 2000))
    checks = {
        "genuine_physical_copy_body_reproduced": encode_packets(
            copy_calibrated_drum_slice(baseline, 9, 1, 10, 1)
        )
        == copied.encoded_body,
        "genuine_before_copy_body_reproduced_by_inverse": inverse.encoded_body
        == baseline.encoded_body,
    }
    if not all(checks.values()):
        raise ValueError("Writer does not reproduce both complete genuine copy-control bodies")
    compiled = compile_edit_plan(source_path, plan_path, output_directory)
    target = decode_artifact(load_artifact(output_directory / "edited.symbols.npz"))
    before, after = sound_data(copied, 24), sound_data(target, 24)
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packet_changes = [i for i, (a, b) in enumerate(zip(copied.packets, target.packets)) if a != b]
    expected_changes = [
        {"offset": 0, "old": 0, "new": 205},
        {"offset": 1, "old": 0, "new": 15},
        {"offset": 4, "old": 208, "new": 157},
        {"offset": 5, "old": 7, "new": 23},
    ]
    checks.update(
        only_existing_destination_packet_changed=packet_changes == [415],
        only_expected_reference_bytes_changed=changes == expected_changes,
        exact_source_reference_copied=after
        == sound_data(copied, 9)
        == bytes.fromhex("cd0f00009d17000000"),
        no_packet_or_body_resizing=len(copied.packets) == len(target.packets) == 543
        and copied.end_byte == target.end_byte == 89844,
        candidate_inverse_reproduces_source=encode_packets(
            copy_calibrated_drum_slice(target, 9, 1, 10, 1)
        )
        == copied.encoded_body,
        all_compiler_roundtrip_checks=compiled["passed"] and all(compiled["checks"].values()),
        source_artifact_preserved=sha256_file(source_path) == evidence["artifact_sha256"],
        source_capture_preserved=sha256_file(capture) == evidence["capture_sha256"],
    )
    report = {
        "analysis_version": "first-generated-cross-drum-slice-copy-0.1",
        "control_evidence_sha256": sha256_file(evidence_path),
        "source_capture_sha256": evidence["capture_sha256"],
        "source_artifact_sha256": evidence["artifact_sha256"],
        "restore_wav_sha256": compiled["restore_wav_sha256"],
        "expected_body_sha256": compiled["target_body_sha256"],
        "source_reference_hex": before.hex(),
        "expected_reference_hex": after.hex(),
        "source_sound_slot": 9,
        "source_slice_key": 2,
        "destination_sound_slot": 10,
        "destination_slice_key": 1,
        "selector_id": 24,
        "start_field": 4045,
        "endpoint_field": 6045,
        "owner_id": 0,
        "reference_byte_changes": changes,
        "changed_plain_packet_indices": packet_changes,
        "checks": checks,
        "passed": all(checks.values()),
        "hardware_verified": False,
        "compiler_report": "compile-report.json",
        "limits": [
            "The physical key1 copy is observed; this generated nonzero-start key2 copy needs its own restore and recapture",
            "Only existing Sound9/keys1 or2 to Sound10/key1 are supported under literal neighboring-reference guards",
            "No sample allocation, arbitrary destination/key mapping, Sound10 endpoint editing or audio preview is enabled",
            "Tone/filter rendering and endpoint inclusivity remain unmeasured",
        ],
    }
    write_bytes(output_directory / "software-validation.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Cross-drum copy candidate checks failed; outputs retained")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.plan, args.out_dir)


if __name__ == "__main__":
    main()
