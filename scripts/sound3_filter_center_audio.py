"""Compare center tone amplitude with prior playback using the unchanged frequency method."""

import argparse
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.prepare_sound3_filter_center import CAPTURE_ID, REGISTRATION
from scripts.sound3_pitch_frequency_analysis import audio_report


def compare_center_audio(reference, center, registration):
    parameters = registration["frequency_method"]["parameters"]
    comparison = registration["neutral_comparison_parameters"]
    if reference["parameters"] != parameters or center["parameters"] != parameters:
        raise ValueError("Frequency method differs from frozen center registration")
    rows = []
    for channel in ("left", "right"):
        a, b = [report["channels"][channel]["measurements"] for report in (reference, center)]
        if len(a) != 3 or len(b) != 3:
            return {
                "hardware_verified": False,
                "measurements": [],
                "all_near_reference_amplitudes_supported": False,
                "comparison_usable": False,
                "filter_writer_enabled": False,
                "reason": "Three usable thresholds required per channel",
            }
        for fraction, x, y in zip(parameters["threshold_peak_fractions"], a, b):
            if x["threshold_peak_fraction"] != fraction or y["threshold_peak_fraction"] != fraction:
                raise ValueError("Center threshold sequence differs from frozen registration")
            amplitudes = [
                float(np.median([fit["fundamental_amplitude"] for fit in item["fits"]]))
                if item["fits"]
                else None
                for item in (x, y)
            ]
            ratio = amplitudes[1] / amplitudes[0] if all(amplitudes) else None
            frequency_delta = (
                y["median_frequency_hz"] / x["median_frequency_hz"] - 1
                if x["median_frequency_hz"] and y["median_frequency_hz"]
                else None
            )
            loop_delta = y["loop_median_seconds"] - x["loop_median_seconds"]
            consistent = (
                reference["passed"]
                and center["passed"]
                and x["usable"]
                and y["usable"]
                and frequency_delta is not None
                and abs(frequency_delta) <= comparison["frequency_relative_tolerance"]
                and abs(loop_delta) <= comparison["loop_seconds_tolerance"]
            )
            rows.append(
                {
                    "channel": channel,
                    "threshold_peak_fraction": fraction,
                    "amplitude_ratio_center_to_prior": ratio,
                    "relative_frequency_delta": frequency_delta,
                    "loop_delta_seconds": loop_delta,
                    "comparison_consistent": consistent,
                    "near_reference_amplitude_supported": consistent
                    and ratio is not None
                    and abs(ratio - 1) <= comparison["amplitude_relative_tolerance"],
                }
            )
    return {
        "hardware_verified": False,
        "measurements": rows,
        "comparison_usable": all(row["comparison_consistent"] for row in rows),
        "all_near_reference_amplitudes_supported": all(
            row["near_reference_amplitude_supported"] for row in rows
        ),
        "broadband_bypass_or_filter_law_confirmed": False,
        "filter_writer_enabled": False,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    directory = root / "experiments" / CAPTURE_ID
    audio_path = directory / "playback.wav"
    measurement_path = directory / "center-frequency-results-001.json"
    output = directory / "center-audio-comparison-results-001.json"
    native_path = directory / "center-native-results-001.json"
    reference_path = root / registration["reference_audio_results"]
    validate_outputs(
        [measurement_path, output],
        [registration_path, audio_path, reference_path, native_path],
        False,
    )
    reference = json.loads(reference_path.read_text())
    native = json.loads(native_path.read_text())
    if (
        sha256_file(reference_path) != registration["reference_audio_results_sha256"]
        or sha256_file(root / registration["reference_audio"])
        != registration["reference_audio_sha256"]
        or sha256_file(root / registration["original_frequency_registration"])
        != registration["original_frequency_registration_sha256"]
        or native["capture_sha256"] != sha256_file(directory / "capture.wav")
        or native["artifact_sha256"] != sha256_file(root / native["artifact_path"])
        or native["registration_sha256"] != sha256_file(registration_path)
    ):
        raise ValueError("Frozen prior audio or native center identity differs")
    center = audio_report(audio_path, registration)
    center["registration_sha256"] = sha256_file(registration_path)
    write_bytes(measurement_path, json_bytes(center))
    result = compare_center_audio(reference, center, registration)
    result.update(
        analysis_version="registered-FILTER-center-to-prior-tone-comparison-0.1",
        registration_sha256=sha256_file(registration_path),
        prior_audio_results_sha256=sha256_file(reference_path),
        center_audio_results_sha256=sha256_file(measurement_path),
        center_native_results_sha256=sha256_file(native_path),
        native_source_and_scope_pass=native["source_body_matches_registration"]
        and native["actual_native_controls_pass"]
        and native["strict_candidate_mask_and_all_other_state_preserved"]
        and native["pitch14_and_volume36_preserved"],
        limits=registration["limits"],
    )
    result["stored_center_and_near_reference_component_supported"] = (
        result["native_source_and_scope_pass"]
        and bool(native["recorded_changes_against_actual_clockwise"]["candidate_changed_steps"])
        and result["comparison_usable"]
        and result["all_near_reference_amplitudes_supported"]
    )
    write_bytes(output, json_bytes(result))
    if not center["passed"]:
        raise ValueError("Frozen center tone measurement unusable; reports retained")


if __name__ == "__main__":
    main()
