"""Evaluate the second start control against its original independent predictions."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_sample_start_control import reference_comparison_checks


def comparison_checks(base, frame, registration):
    checks, packets, changes, values = reference_comparison_checks(base, frame, registration)
    hypotheses = registration["separately_evaluated_hypotheses"]
    first, second = values["after"]["first_u32le"], values["after"]["second_u32le"]
    low, high = hypotheses["first_field_moves_lower"]["expected_range_exclusive"]
    fits = {
        "first_field_moves_lower": low < first < high,
        "second_field_unchanged": second == hypotheses["second_field_unchanged"]["expected_value"],
        "second_field_resets_maximum": second
        == hypotheses["second_field_resets_maximum"]["expected_value"],
    }
    return checks, fits, packets, changes, values


def main():
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments/sound3-start-quarter-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    directory = root / "experiments/event-014-b-sound3-start-quarter"
    baseline_path = directory / registration["baseline_artifact"]
    capture_path = directory / "capture.wav"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    output = root / "experiments/sound3-start-quarter-results-001.json"
    validate_outputs(
        [output], [registration_path, baseline_path, capture_path, artifact_path], False
    )
    source, recorded = load_artifact(baseline_path), load_artifact(artifact_path)
    base, frame = decode_artifact(source), decode_artifact(recorded)
    if (
        sha256_file(baseline_path) != registration["baseline_artifact_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]
    ):
        raise ValueError("Baseline identity differs from preregistration")
    if recorded.metadata["source_sha256"] != sha256_file(capture_path):
        raise ValueError("Recorded artifact does not match capture WAV")
    checks, hypotheses, packets, changes, values = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "second-start-control-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture_path),
        "artifact_sha256": sha256_file(artifact_path),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": hypotheses,
        "any_registered_second_field_hypothesis_fits": hypotheses["second_field_unchanged"]
        or hypotheses["second_field_resets_maximum"],
        "changed_plain_packet_indices": packets,
        "sound3_reference_byte_changes": changes,
        "sound3_header_values": values,
        "observed_second_minus_first": values["after"]["second_u32le"]
        - values["after"]["first_u32le"],
        "native_frame": frame_report(frame),
        "user_report": "done",
        "audition_performed": False,
        "limits": [
            "The first-field range prediction passes; both exact second-field predictions fail",
            "The observed111 difference matches the earlier physical minimum, but was not predicted here",
            "Knob B was left at minimum; automatic endpoint coupling is an inference, not an isolated B experiment",
            "No general minimum-width, knob-angle mapping or endpoint inclusivity rule is established",
            "The public writer remains fixed to start31393; this second start needs a generated-edit hardware test",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Second start preservation checks failed; report retained")


if __name__ == "__main__":
    main()
