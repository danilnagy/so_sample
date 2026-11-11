"""Evaluate fixed swing location and unsigned/signed models without inferring displays."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_swing_max_control import comparison_checks
from scripts.prepare_swing_range_series import CAPTURE_IDS


def series_checks(base, frames, zero, registration, display_values=None):
    if (
        len(frames) != 3
        or len(registration["expected_capture_sequence"]) != 3
        or (display_values is not None and len(display_values) != 3)
    ):
        raise ValueError(
            "Exactly three swing captures and, if supplied, three actual display values required"
        )
    readings = tuple(display_values) if display_values is not None else (None, None, None)
    if any(
        value is not None and (type(value) is not int or not -999 <= value <= 999)
        for value in readings
    ):
        raise ValueError("Actual swing values must be integers; preserve any displayed minus sign")
    previous, legs = base, []
    unsigned, signed = [], []
    for number, (frame, value, expected) in enumerate(
        zip(frames, readings, registration["expected_capture_sequence"]), 1
    ):
        leg_reg = (
            registration
            if number == 1
            else dict(
                registration, baseline_body_sha256=hashlib.sha256(previous.encoded_body).hexdigest()
            )
        )
        controls, fits, observed = comparison_checks(previous, frame, leg_reg)
        observed["independently_reported_display_value"] = value
        raw = observed["candidate_after"]
        unsigned_match = raw == value if value is not None and raw is not None else None
        signed_match = (
            (raw - 256 if raw >= 128 else raw) == value
            if value is not None and raw is not None
            else None
        )
        unsigned.append(unsigned_match)
        signed.append(signed_match)
        expected_sha = expected["expected_body_sha256"]
        numeric_target = expected["requested_display_value"]
        predictions = {
            "body_matches_preregistered_prediction": hashlib.sha256(frame.encoded_body).hexdigest()
            == expected_sha
            if expected_sha is not None
            else None,
            "actual_display_matches_requested_value": value == numeric_target
            if value is not None and numeric_target is not None
            else None,
        }
        legs.append(
            {
                "leg_number": number,
                "experiment_id": expected["experiment_id"],
                "control_checks": controls,
                "location_hypothesis_checks": fits,
                "prediction_hypotheses": predictions,
                "encoding_hypotheses": {
                    "direct_unsigned_byte_matches_display": unsigned_match,
                    "direct_signed_byte_matches_display": signed_match,
                },
                "observed_change": observed,
                "native_frame": frame_report(frame),
            }
        )
        previous = frame
    all_readings = all(value is not None for value in readings)
    encoding_models = {
        "direct_unsigned_supported_across_all_values": all(unsigned) if all_readings else None,
        "direct_signed_supported_across_all_values": all(signed) if all_readings else None,
    }
    returns = {
        "originalS18_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["baseline_body_sha256"],
        "complete_return_body_equals_originalS18": frames[-1].encoded_body == base.encoded_body,
        "complete_return_plain_packets_equal_originalS18": frames[-1].packets == base.packets,
        "original_zero_body_matches_registration": hashlib.sha256(zero.encoded_body).hexdigest()
        == registration["original_zero_body_sha256"],
        "minimum0_complete_body_equals_original_zero_state": frames[0].encoded_body
        == zero.encoded_body
        if readings[0] == 0
        else None,
        "minimum_display_not_above_requested9_and_observed18": readings[0] <= 9
        if readings[0] is not None
        else None,
    }
    controls_passed = all(all(leg["control_checks"].values()) for leg in legs)
    location_passed = all(
        all(
            value is True
            for key, value in leg["location_hypothesis_checks"].items()
            if key != "candidate_equals_independently_reported_display_value"
        )
        for leg in legs
    )
    predictions_passed = all(
        all(value is True for value in leg["prediction_hypotheses"].values()) for leg in legs[1:]
    )
    required_returns = all(
        value is True
        for key, value in returns.items()
        if key != "minimum0_complete_body_equals_original_zero_state"
    )
    conditional_zero = returns["minimum0_complete_body_equals_original_zero_state"] is not False
    supported = (
        controls_passed
        and location_passed
        and predictions_passed
        and required_returns
        and conditional_zero
        and any(value is True for value in encoding_models.values())
    )
    return {
        "legs": legs,
        "encoding_models": encoding_models,
        "return_hypotheses": returns,
        "control_passed": controls_passed,
        "series_supported": supported,
        "numeric_percentage_or_timing_units_confirmed": False,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, nargs=3)
    parser.add_argument("--display-values", type=int, nargs=3)
    args = parser.parse_args()
    paths = args.artifacts or [
        folder / "derived/analysis-001/capture.symbols.npz" for folder in directories
    ]
    registration_path = root / "experiments/swing-range-series-registration-001.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["baseline_artifact"]
    zero_path = root / registration["original_zero_artifact"]
    captures = [folder / "capture.wav" for folder in directories]
    output = root / "experiments/swing-range-series-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, zero_path, *paths, *captures], False
    )
    recorded = [load_artifact(path) for path in paths]
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(root / registration["baseline_capture"])
        != registration["baseline_capture_sha256"]
        or sha256_file(zero_path) != registration["original_zero_artifact_sha256"]
        or any(
            item.metadata["source_sha256"] != sha256_file(capture)
            for item, capture in zip(recorded, captures)
        )
    ):
        raise ValueError("Registered swing sources or series capture identities differ")
    base, zero = [decode_artifact(load_artifact(path)) for path in (source_path, zero_path)]
    report = series_checks(
        base, [decode_artifact(item) for item in recorded], zero, registration, args.display_values
    )
    report.update(
        analysis_version="swing-minimum-middle9-and-exact18-return-control-check-0.1",
        registration_sha256=sha256_file(registration_path),
        captures=[
            {
                "experiment_id": folder.name,
                "capture_sha256": sha256_file(capture),
                "artifact_sha256": sha256_file(path),
                "artifact_path": str(path),
            }
            for folder, capture, path in zip(directories, captures, paths)
        ],
        swing_writer_enabled=False,
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Swing series core invariants failed; report retained")


if __name__ == "__main__":
    main()
