"""Check literal center data against both scalar orders, without endpoint fitting."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_probe import recorded_report
from scripts.check_sound3_filter_range import alternative_values, mask_preserved
from scripts.prepare_sound3_filter_center import CAPTURE_ID, REGISTRATION


def center_report(base, center, registration):
    report = recorded_report(base, center, registration)
    values = report["raw_Sound3_fields"]["after"]["uninterpreted_candidate_values"]
    alternative = alternative_values(center)
    scope = all(report["preservation_checks"].values()) and mask_preserved(base, center)
    return {
        "source_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "actual_native_controls_pass": all(report["native_checks"].values()),
        "strict_candidate_mask_and_all_other_state_preserved": scope,
        "pitch14_and_volume36_preserved": report["raw_Sound3_fields"]["after"]["first_low5_values"]
        == registration["expected_pitch_values"]
        and report["raw_Sound3_fields"]["after"]["volume_values"]
        == registration["expected_volume_values"],
        "raw_contiguous_values": values,
        "raw_alternative_values": alternative,
        "values_uniform": len(set(values)) == 1,
        "monotonic_scalar_order_checks": {
            "all_contiguous_values_between_endpoints": scope
            and all(
                registration["contiguous_endpoint_values"][0]
                < value
                < registration["contiguous_endpoint_values"][1]
                for value in values
            ),
            "all_alternative_values_between_endpoints": scope
            and all(
                registration["alternative_endpoint_values"][0]
                < value
                < registration["alternative_endpoint_values"][1]
                for value in alternative
            ),
        },
        "recorded_changes_against_actual_clockwise": report,
        "center_code_guessed": False,
        "filter_general_model_or_units_confirmed": False,
        "filter_writer_enabled": False,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    directory = root / "experiments" / CAPTURE_ID
    source_path = root / registration["source_artifact"]
    capture_path = directory / "capture.wav"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    observation_path = (
        root
        / "experiments/event-057-d-return-sound3-filter-A-lock-up/hardware-observation-001.json"
    )
    output = directory / "center-native-results-001.json"
    validate_outputs([output], [registration_path, source_path, capture_path, artifact_path], False)
    recorded = load_artifact(artifact_path)
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
        or sha256_file(observation_path) != registration["source_observation_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture_path)
    ):
        raise ValueError("Registered FILTER source or independent center identity differs")
    base, actual = [decode_artifact(item) for item in (load_artifact(source_path), recorded)]
    report = center_report(base, actual, registration)
    report.update(
        analysis_version="FILTER-interior-native-and-two-scalar-order-check-0.1",
        hardware_verified=False,
        registration_sha256=sha256_file(registration_path),
        capture_sha256=sha256_file(capture_path),
        artifact_sha256=sha256_file(artifact_path),
        artifact_path=artifact_path.relative_to(root).as_posix(),
        native_frame=frame_report(actual),
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if not report["source_body_matches_registration"] or not report["actual_native_controls_pass"]:
        raise ValueError("Native FILTER center control failed; report retained")


if __name__ == "__main__":
    main()
