"""Check fine-tempo endpoints and whole-state return without fitting or inferred displays."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo_control import comparison_checks
from scripts.prepare_fine_tempo_range_series import CAPTURE_IDS


def range_series_checks(base, frames, registration, display_bpms=None):
    if (
        len(frames) != 3
        or len(registration["expected_capture_sequence"]) != 3
        or (display_bpms is not None and len(display_bpms) != 3)
    ):
        raise ValueError(
            "Exactly three captures and, if supplied, three actual display readings required"
        )
    readings = tuple(display_bpms) if display_bpms is not None else (None, None, None)
    previous, previous_display = base, 100
    legs = []
    for number, (frame, display, expected) in enumerate(
        zip(frames, readings, registration["expected_capture_sequence"]), 1
    ):
        leg_reg = (
            registration
            if number == 1
            else dict(
                registration, baseline_body_sha256=hashlib.sha256(previous.encoded_body).hexdigest()
            )
        )
        controls, fits, observed = comparison_checks(
            previous, frame, leg_reg, previous_display, display
        )
        hypotheses = {
            "body_matches_preregistered_prediction": hashlib.sha256(frame.encoded_body).hexdigest()
            == expected["expected_body_sha256"],
            "actual_display_matches_requested_value": display == expected["expected_after_bpm"]
            if display is not None
            else None,
            "single_byte_hypothesis_supported": observed["single_byte_hypothesis_status"]
            == "supported_for_this_transition",
        }
        legs.append(
            {
                "leg_number": number,
                "experiment_id": expected["experiment_id"],
                "control_checks": controls,
                "tempo_hypothesis_checks": fits,
                "prediction_hypotheses": hypotheses,
                "observed_change": observed,
                "native_frame": frame_report(frame),
            }
        )
        previous, previous_display = frame, display
    return_checks = {
        "original100_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["baseline_body_sha256"],
        "entire_return_body_equals_independent_original100": frames[-1].encoded_body
        == base.encoded_body,
        "entire_return_plain_packets_equal_independent_original100": frames[-1].packets
        == base.packets,
    }
    controls_passed = all(all(leg["control_checks"].values()) for leg in legs)
    supported = (
        controls_passed
        and all(return_checks.values())
        and all(
            all(value is True for value in leg["prediction_hypotheses"].values()) for leg in legs
        )
    )
    return {
        "legs": legs,
        "return_hypotheses": return_checks,
        "control_passed": controls_passed,
        "series_supported": supported,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, nargs=3)
    parser.add_argument("--display-bpms", type=int, nargs=3)
    args = parser.parse_args()
    paths = args.artifacts or [
        folder / "derived/analysis-001/capture.symbols.npz" for folder in directories
    ]
    registration_path = root / "experiments/fine-tempo-range-series-registration-001.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["baseline_artifact"]
    source_capture = root / registration["baseline_capture"]
    captures = [folder / "capture.wav" for folder in directories]
    output = root / "experiments/fine-tempo-range-series-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, source_capture, *paths, *captures], False
    )
    recorded = [load_artifact(path) for path in paths]
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(source_capture) != registration["baseline_capture_sha256"]
        or any(
            artifact.metadata["source_sha256"] != sha256_file(capture)
            for artifact, capture in zip(recorded, captures)
        )
    ):
        raise ValueError("Registered source or range-series capture identities differ")
    base = decode_artifact(load_artifact(source_path))
    report = range_series_checks(
        base, [decode_artifact(item) for item in recorded], registration, args.display_bpms
    )
    report.update(
        analysis_version="fine-tempo-endpoints-and-original100-return-control-check-0.1",
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
        fine_tempo_writer_enabled=False,
        public_tempo_scope="Observed presets80/120/140 only",
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Fine-tempo range-series core controls failed; report retained")


if __name__ == "__main__":
    main()
