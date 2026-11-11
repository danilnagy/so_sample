"""Evaluate the fixed-start minimum control while retaining exact prediction failures."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_sample_start_control import reference_comparison_checks


def comparison_checks(base, frame, registration):
    checks, packets, changes, values = reference_comparison_checks(base, frame, registration)
    first, second = values["after"]["first_u32le"], values["after"]["second_u32le"]
    checks["first_field_unchanged"] = (
        values["before"]["first_u32le"]
        == first
        == registration["control_checks"]["first_field_unchanged"]
    )
    hypotheses = registration["separately_evaluated_hypotheses"]
    hypothesis_checks = {
        "second_field_is_length": second == hypotheses["second_field_is_length"]["expected_value"],
        "second_field_is_endpoint": second
        == hypotheses["second_field_is_endpoint"]["expected_value"]
        and second - first == hypotheses["second_field_is_endpoint"]["expected_second_minus_first"],
    }
    return checks, hypothesis_checks, packets, changes, values


def main():
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments/sound3-start-min-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    directory = root / "experiments/event-013-b-sound3-start-min"
    base_path = directory / registration["baseline_artifact"]
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    output = root / "experiments/sound3-start-min-results-001.json"
    validate_outputs([output], [registration_path, base_path, artifact_path, capture], False)
    source, recorded = load_artifact(base_path), load_artifact(artifact_path)
    base, frame = decode_artifact(source), decode_artifact(recorded)
    if sha256_file(base_path) != registration["baseline_artifact_sha256"]:
        raise ValueError("Baseline artifact does not match registration")
    if source.metadata["source_sha256"] != registration["baseline_source_sha256"]:
        raise ValueError("Baseline source identity differs")
    if hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]:
        raise ValueError("Baseline body differs")
    if recorded.metadata["source_sha256"] != sha256_file(capture):
        raise ValueError("Recorded artifact does not match capture WAV")
    checks, hypotheses, packets, changes, values = comparison_checks(base, frame, registration)
    first, second = values["after"]["first_u32le"], values["after"]["second_u32le"]
    report = {
        "analysis_version": "nonzero-start-minimum-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": hypotheses,
        "any_registered_exact_hypothesis_fits": any(hypotheses.values()),
        "changed_plain_packet_indices": packets,
        "sound3_reference_byte_changes": changes,
        "sound3_header_values": values,
        "observed_second_minus_first": second - first,
        "native_frame": frame_report(frame),
        "user_report": "done",
        "nonzero_start_writer_enabled": False,
        "limits": [
            "The exact registered79 and31472 predictions are evaluated separately; observed31504 is not substituted into them",
            "A broader endpoint interpretation is plausible from the proximity to start, but remains an inference pending an acoustic discriminator",
            "The difference111 does not establish a general minimum-width rule or inclusive/exclusive endpoint",
            "This is a physical trim control; no generated nonzero-start edit has been tested",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Fixed-start minimum preservation checks failed; report retained")


if __name__ == "__main__":
    main()
