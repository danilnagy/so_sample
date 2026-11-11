"""Evaluate frozen straight-versus-swing6 onset hypotheses without fitting units."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.prepare_swing_timing_pair import DIRECTORIES


def compare_reports(straight, swung, registration):
    parameters = registration["parameters"]
    baseline = registration["straight_reference_hypotheses"]
    hypothesis = registration["comparison_hypotheses"]
    if straight["parameters"] != parameters or swung["parameters"] != parameters:
        raise ValueError("Timing parameters differ from frozen registration")
    results = []
    for name in ("left", "right"):
        a, b = [report["channels"][name]["measurements"] for report in (straight, swung)]
        if len(a) != 3 or len(b) != 3:
            raise ValueError("All three registered thresholds required in both channels")
        for fraction, x, y in zip(parameters["threshold_peak_fractions"], a, b):
            if x["threshold_peak_fraction"] != fraction or y["threshold_peak_fraction"] != fraction:
                raise ValueError("Threshold sequence differs from registration")
            short_delta = y["short_gap_median_seconds"] - x["short_gap_median_seconds"]
            long_delta = y["long_gap_median_seconds"] - x["long_gap_median_seconds"]
            loop_delta = y["loop_median_seconds"] - x["loop_median_seconds"]
            checks = {
                "straight_short_gap_matches5_steps": abs(
                    x["short_gap_median_seconds"]
                    - x["loop_median_seconds"] * baseline["short_gap_loop_fraction"]
                )
                <= baseline["gap_tolerance_seconds"],
                "straight_long_gap_matches11_steps": abs(
                    x["long_gap_median_seconds"]
                    - x["loop_median_seconds"] * baseline["long_gap_loop_fraction"]
                )
                <= baseline["gap_tolerance_seconds"],
                "swing_short_gap_increases": short_delta
                > hypothesis["swing6_short_gap_increases_seconds_minimum"],
                "swing_long_gap_decreases": long_delta
                < -hypothesis["swing6_long_gap_decreases_seconds_minimum"],
                "whole_loop_period_preserved": abs(loop_delta)
                <= hypothesis["loop_period_difference_seconds_maximum"],
                "opposite_gap_changes_balance": abs(short_delta + long_delta)
                <= hypothesis["opposite_gap_changes_sum_seconds_maximum"],
            }
            results.append(
                {
                    "channel": name,
                    "threshold_peak_fraction": fraction,
                    "short_gap_delta_seconds": short_delta,
                    "long_gap_delta_seconds": long_delta,
                    "loop_delta_seconds": loop_delta,
                    "checks": checks,
                }
            )
    return {
        "all_input_consistency_checks": straight["passed"] and swung["passed"],
        "measurements": results,
        "timing_hypotheses_supported": straight["passed"]
        and swung["passed"]
        and all(all(item["checks"].values()) for item in results),
        "hardware_verified": False,
        "numeric_timing_units_confirmed": False,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments/swing-timing-measurement-registration-001.json"
    registration = json.loads(registration_path.read_text())
    directories = [root / "experiments" / name for name in DIRECTORIES]
    paths = [directory / "playback-timing-results-001.json" for directory in directories]
    output = root / "experiments/swing-timing-pair-audio-results-001.json"
    validate_outputs([output], [registration_path, *paths], False)
    reports = [json.loads(path.read_text()) for path in paths]
    for directory, report in zip(directories, reports):
        if report["source_sha256"] != sha256_file(directory / "playback.wav") or report[
            "registration_sha256"
        ] != sha256_file(registration_path):
            raise ValueError("Timing report audio or method fingerprint differs")
        native_path = directory / "hardware-recapture-results-001.json"
        native = json.loads(native_path.read_text())
        if (
            not native["passed"]
            or native["capture_sha256"] != sha256_file(directory / "capture.wav")
            or native["artifact_sha256"] != sha256_file(root / native["artifact_path"])
        ):
            raise ValueError("Exact native recapture required before audio comparison")
    if reports[0]["source_sha256"] != registration["straight_playback_sha256"]:
        raise ValueError("Straight reference differs from frozen method calibration")
    if (
        sha256_file(directories[0] / "hardware-recapture-results-001.json")
        != registration["straight_backup_results_sha256"]
        or sha256_file(root / "experiments/swing-timing-pair-registration-001.json")
        != registration["pair_registration_sha256"]
    ):
        raise ValueError("Frozen native reference or original pair registration differs")
    result = compare_reports(*reports, registration)
    result.update(
        analysis_version="registered-swing0-versus6-audio-comparison-0.1",
        registration_sha256=sha256_file(registration_path),
        input_reports_sha256=[sha256_file(path) for path in paths],
    )
    write_bytes(output, json_bytes(result))
    print(
        json.dumps(
            {
                "timing_hypotheses_supported": result["timing_hypotheses_supported"],
                "hardware_verified": False,
            }
        )
    )


if __name__ == "__main__":
    main()
