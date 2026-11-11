"""Evaluate the registered nonzero-start drum key2 control without changing predictions."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_slice_control import reference_comparison_checks


def comparison_checks(base, frame, registration):
    checks, packets, selectors, changes, values = reference_comparison_checks(
        base, frame, registration
    )
    hypotheses = registration["separately_evaluated_hypotheses"]
    low, high = hypotheses["second_field_moves_lower_but_above_first"]["expected_range_exclusive"]
    fits = {
        "key2_maps_to_selector9": selectors
        == hypotheses["key2_maps_to_selector9"]["expected_changed_selector_ids"],
        "first_field_unchanged": values is not None
        and values["before"]["first_u32le"]
        == values["after"]["first_u32le"]
        == hypotheses["first_field_unchanged"]["expected_value"],
        "second_field_is_length": values is not None
        and values["after"]["second_u32le"]
        == hypotheses["second_field_is_length"]["expected_value"],
        "second_field_is_endpoint": values is not None
        and values["after"]["second_u32le"]
        == hypotheses["second_field_is_endpoint"]["expected_value"]
        and values["after"]["second_u32le"] - values["after"]["first_u32le"]
        == hypotheses["second_field_is_endpoint"]["expected_second_minus_first"],
        "second_field_moves_lower_but_above_first": values is not None
        and low < values["after"]["second_u32le"] < high,
    }
    return checks, fits, packets, selectors, changes, values


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-017-b-drum9-key2-trim-min"
    registration_path = root / "experiments/drum9-key2-trim-min-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    source_path = directory / registration["baseline_artifact"]
    capture = directory / "capture.wav"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    output = root / "experiments/drum9-key2-trim-min-results-001.json"
    validate_outputs([output], [registration_path, source_path, capture, artifact_path], False)
    source, recorded = load_artifact(source_path), load_artifact(artifact_path)
    base, frame = decode_artifact(source), decode_artifact(recorded)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Source or recorded capture identity differs from registration")
    checks, fits, packets, selectors, changes, values = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "nonzero-start-drum-key2-control-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "changed_plain_packet_indices": packets,
        "changed_selector_ids": selectors,
        "reference_byte_changes": changes,
        "reference_values": values,
        "native_frame": frame_report(frame),
        "user_report": "done and confirmed I hear a click",
        "audition_observation_file": "event-017-b-drum9-key2-trim-min/audition-observation.json",
        "nonzero_start_drum_writer_enabled": False,
        "limits": [
            "Key2 maps to selector9; first4045 remains and second4172 matches the exact registered endpoint hypothesis",
            "The mutually alternative literal-length127 hypothesis fails and is retained",
            "The reported click supports a short endpoint window; exact hardware duration and inclusivity are not measured",
            "The127 difference is locally observed at two starts but is not a general minimum-width rule",
            "No generated key2 edit has been restored; other drum keys, starts and sound slots remain unverified",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Key2 reference preservation checks failed; report retained")


if __name__ == "__main__":
    main()
