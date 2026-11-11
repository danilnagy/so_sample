"""Compile the first Sound9/key1 endpoint candidate from the reviewed minimum."""

import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.drums import calibrated_drum_slice, replace_calibrated_drum_slice_end
from po33_re.formats.packets import decode_artifact, encode_packets, sound_data
from po33_re.formats.patterns import pattern_data
from po33_re.formats.samples import decode_signed_mulaw
from po33_re.modem.symbols import load_artifact


def run(plan_path, output_directory):
    root = Path(__file__).resolve().parents[1]
    evidence_path = root / "experiments/drum9-key1-trim-min-results-001.json"
    registration_path = root / "experiments/drum9-key1-trim-min-predictions-001.json"
    evidence, registration = [json.loads(p.read_text()) for p in (evidence_path, registration_path)]
    if (
        not evidence["control_passed"]
        or not evidence["hypothesis_checks"]["key1_maps_to_selector8"]
    ):
        raise ValueError("Reviewed key1 mapping and locality evidence required")
    source_path = (
        root
        / "experiments/event-016-b-drum9-key1-trim-min/derived/analysis-001/capture.symbols.npz"
    )
    copy_path = (source_path.parents[2] / registration["baseline_artifact"]).resolve()
    if (
        sha256_file(source_path) != evidence["artifact_sha256"]
        or sha256_file(copy_path) != registration["baseline_artifact_sha256"]
    ):
        raise ValueError("Minimum/copy artifacts differ from reviewed identities")
    source = load_artifact(source_path)
    minimum, original_copy = decode_artifact(source), decode_artifact(load_artifact(copy_path))
    if (
        hashlib.sha256(minimum.encoded_body).hexdigest()
        != evidence["native_frame"]["encoded_body_sha256"]
        or source.metadata["source_sha256"] != evidence["capture_sha256"]
    ):
        raise ValueError("Minimum body/source differs from reviewed control")
    plan = json.loads(plan_path.read_text())
    if plan.get("operations") != [
        {"operation": "set_drum_slice_end", "sound": 9, "slice": 1, "end": 2000}
    ]:
        raise ValueError("This experiment requires exactly the Sound9/key1 endpoint2000 operation")
    checks = {
        "genuine_minimum_forward_body_reproduced": encode_packets(
            replace_calibrated_drum_slice_end(original_copy, 9, 1, 127)
        )
        == minimum.encoded_body,
        "genuine_copy_inverse_body_reproduced": encode_packets(
            replace_calibrated_drum_slice_end(minimum, 9, 1, 4044)
        )
        == original_copy.encoded_body,
    }
    if not all(checks.values()):
        raise ValueError("Writer does not reproduce both complete genuine bodies")
    compiled = compile_edit_plan(source_path, plan_path, output_directory)
    target = decode_artifact(load_artifact(output_directory / "edited.symbols.npz"))
    before, after = sound_data(minimum, 8), sound_data(target, 8)
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packet_changes = [i for i, (a, b) in enumerate(zip(minimum.packets, target.packets)) if a != b]
    checks.update(
        only_reference_packet_changed=packet_changes == [383],
        only_expected_endpoint_bytes_changed=changes
        == [{"offset": 4, "old": 127, "new": 208}, {"offset": 5, "old": 0, "new": 7}],
        start_and_owner_preserved=before[:4] == after[:4] == bytes(4)
        and before[8:] == after[8:] == b"\0",
        exact_candidate_reference=after.hex() == "00000000d007000000",
        backing_codes_preserved=sound_data(minimum, 0) == sound_data(target, 0),
        all_patterns_preserved=all(
            pattern_data(minimum, p) == pattern_data(target, p) for p in range(1, 17)
        ),
        candidate_inverse_reproduces_source=encode_packets(
            replace_calibrated_drum_slice_end(target, 9, 1, 127)
        )
        == minimum.encoded_body,
        all_compiler_roundtrip_checks=compiled["passed"] and all(compiled["checks"].values()),
        source_file_preserved=sha256_file(source_path) == evidence["artifact_sha256"],
    )
    _, start, end, owner = calibrated_drum_slice(target, 9, 1)
    codes = np.frombuffer(owner[9:], dtype=np.uint8)
    audio = resample_poly(decode_signed_mulaw(codes[start:end]), 256, 125)
    buffer = io.BytesIO()
    sf.write(buffer, audio, 48000, format="WAV", subtype="FLOAT")
    preview_path = output_directory / "slice-preview-48k.wav"
    report_path = output_directory / "software-validation.json"
    validate_outputs(
        [preview_path, report_path],
        [source_path, copy_path, plan_path, evidence_path, registration_path],
        False,
    )
    write_bytes(preview_path, buffer.getvalue())
    checks["preview_frame_count"] = len(audio) == 4096
    report = {
        "analysis_version": "first-drum-slice-candidate-0.1",
        "minimum_control_evidence_sha256": sha256_file(evidence_path),
        "source_capture_sha256": evidence["capture_sha256"],
        "source_artifact_sha256": evidence["artifact_sha256"],
        "restore_wav_sha256": compiled["restore_wav_sha256"],
        "expected_body_sha256": compiled["target_body_sha256"],
        "expected_reference_hex": after.hex(),
        "sound_slot": 9,
        "slice_key": 1,
        "selector_id": 8,
        "start_field": start,
        "endpoint_field": end,
        "reference_byte_changes": changes,
        "changed_plain_packet_indices": packet_changes,
        "checks": checks,
        "passed": all(checks.values()),
        "hardware_verified": False,
        "compiler_report": "compile-report.json",
        "preview": {
            "raw_code_count": 2000,
            "sample_rate_hz_nominal": 23437.5,
            "export_sample_rate_hz": 48000,
            "export_frames": len(audio),
            "selection_policy": "Explicit half-open[start,end); exact device inclusivity unresolved",
            "pitch_and_gain_applied": False,
        },
        "limits": [
            "Only Sound9/key1 at start0/owner0 with the exact observed other15 references is supported",
            "The local endpoint guard127..4044 does not establish a general drum minimum or endpoint inclusivity",
            "The exact79 prediction remains failed; this first generated drum edit needs its own restore, recapture and audition test",
            "The preview is an unpitched raw-code selection; the project exporter still provides no drum audio previews",
        ],
    }
    write_bytes(report_path, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Drum candidate checks failed; diagnostic outputs retained")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.plan, args.out_dir)


if __name__ == "__main__":
    main()
