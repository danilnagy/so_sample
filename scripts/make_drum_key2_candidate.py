"""Compile one nonzero-start drum candidate from reviewed field and audition evidence."""

import argparse
import hashlib
import io
import json
from pathlib import Path

import soundfile as sf
from scipy.signal import resample_poly

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.drums import replace_calibrated_drum_slice_end
from po33_re.formats.packets import decode_artifact, encode_packets, sound_data
from po33_re.formats.samples import extract_calibrated_drum_slice_sound
from po33_re.modem.symbols import load_artifact


def run(plan_path, output_directory):
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-017-b-drum9-key2-trim-min"
    source_path = directory / "derived/analysis-001/capture.symbols.npz"
    evidence_path = root / "experiments/drum9-key2-trim-min-results-001.json"
    registration_path = root / "experiments/drum9-key2-trim-min-predictions-001.json"
    audition_path = directory / "audition-observation.json"
    evidence, registration, audition = [
        json.loads(p.read_text()) for p in (evidence_path, registration_path, audition_path)
    ]
    if (
        not evidence["control_passed"]
        or not evidence["hypothesis_checks"]["key2_maps_to_selector9"]
        or not evidence["hypothesis_checks"]["second_field_is_endpoint"]
        or audition["classification"] != "very_short_click_or_burst"
        or audition["capture_sha256"] != evidence["capture_sha256"]
    ):
        raise ValueError(
            "Reviewed key2 mapping, endpoint hypothesis and matching click report required"
        )
    baseline_path = directory / registration["baseline_artifact"]
    if (
        sha256_file(source_path) != evidence["artifact_sha256"]
        or sha256_file(baseline_path) != registration["baseline_artifact_sha256"]
    ):
        raise ValueError("Minimum/baseline artifacts differ from reviewed identities")
    source = load_artifact(source_path)
    minimum, baseline = decode_artifact(source), decode_artifact(load_artifact(baseline_path))
    if (
        hashlib.sha256(minimum.encoded_body).hexdigest()
        != evidence["native_frame"]["encoded_body_sha256"]
        or source.metadata["source_sha256"] != evidence["capture_sha256"]
    ):
        raise ValueError("Minimum body/source differs from reviewed control")
    plan = json.loads(plan_path.read_text())
    if plan.get("operations") != [
        {"operation": "set_drum_slice_end", "sound": 9, "slice": 2, "end": 6045}
    ]:
        raise ValueError("This experiment requires exactly the Sound9/key2 endpoint6045 operation")
    checks = {
        "genuine_minimum_forward_body_reproduced": encode_packets(
            replace_calibrated_drum_slice_end(baseline, 9, 2, 4172)
        )
        == minimum.encoded_body,
        "genuine_baseline_inverse_body_reproduced": encode_packets(
            replace_calibrated_drum_slice_end(minimum, 9, 2, 8088)
        )
        == baseline.encoded_body,
    }
    if not all(checks.values()):
        raise ValueError("Writer does not reproduce both complete genuine endpoint bodies")
    compiled = compile_edit_plan(source_path, plan_path, output_directory)
    target = decode_artifact(load_artifact(output_directory / "edited.symbols.npz"))
    before, after = sound_data(minimum, 9), sound_data(target, 9)
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packet_changes = [i for i, (a, b) in enumerate(zip(minimum.packets, target.packets)) if a != b]
    checks.update(
        only_key2_reference_packet_changed=packet_changes == [385],
        only_expected_endpoint_bytes_changed=changes
        == [{"offset": 4, "old": 76, "new": 157}, {"offset": 5, "old": 16, "new": 23}],
        exact_candidate_reference=after.hex() == "cd0f00009d17000000",
        start_and_owner_preserved=before[:4] == after[:4] and before[8:] == after[8:] == b"\0",
        accepted_key1_preserved=sound_data(minimum, 8)
        == sound_data(target, 8)
        == bytes.fromhex("00000000d007000000"),
        candidate_inverse_reproduces_source=encode_packets(
            replace_calibrated_drum_slice_end(target, 9, 2, 4172)
        )
        == minimum.encoded_body,
        all_compiler_roundtrip_checks=compiled["passed"] and all(compiled["checks"].values()),
        source_file_preserved=sha256_file(source_path) == evidence["artifact_sha256"],
    )
    audio, preview = extract_calibrated_drum_slice_sound(target, 9, 2)
    audio = resample_poly(audio, 256, 125)
    buffer = io.BytesIO()
    sf.write(buffer, audio, 48000, format="WAV", subtype="FLOAT")
    preview_path, report_path = (
        output_directory / "slice-preview-48k.wav",
        output_directory / "software-validation.json",
    )
    validate_outputs(
        [preview_path, report_path],
        [source_path, baseline_path, plan_path, evidence_path, audition_path],
        False,
    )
    write_bytes(preview_path, buffer.getvalue())
    checks["preview_frame_count"] = len(audio) == 4096
    report = {
        "analysis_version": "nonzero-start-drum-key2-candidate-0.1",
        "control_evidence_sha256": sha256_file(evidence_path),
        "audition_observation_sha256": sha256_file(audition_path),
        "source_capture_sha256": evidence["capture_sha256"],
        "source_artifact_sha256": evidence["artifact_sha256"],
        "restore_wav_sha256": compiled["restore_wav_sha256"],
        "expected_body_sha256": compiled["target_body_sha256"],
        "expected_reference_hex": after.hex(),
        "sound_slot": 9,
        "slice_key": 2,
        "selector_id": 9,
        "start_field": 4045,
        "endpoint_field": 6045,
        "reference_byte_changes": changes,
        "changed_plain_packet_indices": packet_changes,
        "checks": checks,
        "passed": all(checks.values()),
        "hardware_verified": False,
        "compiler_report": "compile-report.json",
        "preview": {**preview, "export_sample_rate_hz": 48000, "export_frames": len(audio)},
        "limits": [
            "Only Sound9/keys1 and2 at their separate fixed-start intervals are supported, with the literal other14 references",
            "The reported key2 click and exact endpoint prediction support a local interpretation; this new generated nonzero-start edit needs its own hardware test",
            "General minima, arbitrary starts, other keys/drum slots and exact endpoint inclusivity remain unresolved",
            "The standalone key2 preview is unpitched half-open raw-code extraction; project previews require their own explicit opt-in and calibration context",
        ],
    }
    write_bytes(report_path, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Nonzero-start drum candidate checks failed; outputs retained")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.plan, args.out_dir)


if __name__ == "__main__":
    main()
