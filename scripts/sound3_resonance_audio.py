"""Use the unchanged common tone method for the preregistered B0/B63 comparison."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.prepare_generated_sound3_resonance_pair import DIRECTORIES, REGISTRATION
from scripts.sound3_pitch_frequency_analysis import audio_report


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def reference_audio_supported(report, registration):
    parameters = registration["frequency_method"]["parameters"]
    limits = registration["resonance_comparison_parameters"]
    if report["parameters"] != parameters:
        raise ValueError("Resonance method differs from frozen registration")
    if not report["passed"]:
        return False
    for channel in ("left", "right"):
        rows = report["channels"][channel]["measurements"]
        if len(rows) != 3:
            return False
        for fraction, row in zip(parameters["threshold_peak_fractions"], rows):
            frequency = row["median_frequency_hz"]
            if (
                row["threshold_peak_fraction"] != fraction
                or not row["usable"]
                or not finite(frequency)
                or abs(frequency / limits["reference_frequency_lead_hz"] - 1)
                > limits["frequency_relative_tolerance"]
            ):
                return False
    return True


def compare_resonance_audio(reference, candidate, registration):
    parameters = registration["frequency_method"]["parameters"]
    limits = registration["resonance_comparison_parameters"]
    if reference["parameters"] != parameters or candidate["parameters"] != parameters:
        raise ValueError("Resonance method differs from frozen registration")
    reference_supported = reference_audio_supported(reference, registration)
    rows = []
    for channel in ("left", "right"):
        a, b = [report["channels"][channel]["measurements"] for report in (reference, candidate)]
        if len(a) != 3 or len(b) != 3:
            return {
                "hardware_verified": False,
                "measurements": [],
                "comparison_usable": False,
                "all_amplitude_increases_supported": False,
                "resonance_writer_enabled": False,
                "reason": "Three usable thresholds required per channel",
            }
        for fraction, x, y in zip(parameters["threshold_peak_fractions"], a, b):
            if x["threshold_peak_fraction"] != fraction or y["threshold_peak_fraction"] != fraction:
                raise ValueError("Resonance threshold sequence differs from registration")
            amplitudes = [
                float(np.median([fit["fundamental_amplitude"] for fit in item["fits"]]))
                if item["fits"]
                else None
                for item in (x, y)
            ]
            ratio = (
                amplitudes[1] / amplitudes[0]
                if all(finite(value) and value > 0 for value in amplitudes)
                else None
            )
            frequencies = [item["median_frequency_hz"] for item in (x, y)]
            frequency_delta = (
                frequencies[1] / frequencies[0] - 1
                if all(finite(value) and value > 0 for value in frequencies)
                else None
            )
            loops = [item["loop_median_seconds"] for item in (x, y)]
            loop_delta = loops[1] - loops[0] if all(finite(value) for value in loops) else None
            usable = (
                reference_supported
                and candidate["passed"]
                and x["usable"]
                and y["usable"]
                and ratio is not None
                and frequency_delta is not None
                and loop_delta is not None
                and abs(frequency_delta) <= limits["frequency_relative_tolerance"]
                and abs(loop_delta) <= limits["loop_seconds_tolerance"]
            )
            rows.append(
                {
                    "channel": channel,
                    "threshold_peak_fraction": fraction,
                    "amplitude_ratio_candidate_to_reference": ratio,
                    "relative_frequency_delta": frequency_delta,
                    "loop_delta_seconds": loop_delta,
                    "comparison_consistent": usable,
                    "amplitude_increase_supported": usable
                    and ratio >= 1 + limits["minimum_amplitude_increase_fraction"],
                }
            )
    return {
        "hardware_verified": False,
        "measurements": rows,
        "comparison_usable": all(row["comparison_consistent"] for row in rows),
        "all_amplitude_increases_supported": all(
            row["amplitude_increase_supported"] for row in rows
        ),
        "general_resonance_law_or_broad_spectral_response_confirmed": False,
        "resonance_writer_enabled": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leg", choices=("reference", "candidate"), required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    index = ("reference", "candidate").index(args.leg)
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    folder = root / "experiments" / DIRECTORIES[index]
    audio_path = folder / "playback.wav"
    native_path = folder / "hardware-recapture-results-001.json"
    output = folder / "resonance-frequency-results-001.json"
    comparison_path = root / "experiments/sound3-generated-B0-B63-audio-results-001.json"
    validate_outputs(
        [output] + ([comparison_path] if index else []),
        [registration_path, audio_path, native_path],
        False,
    )
    native = json.loads(native_path.read_text())
    if (
        not native["passed"]
        or not all(native["checks"].values())
        or native["registration_sha256"] != sha256_file(registration_path)
        or native["capture_sha256"] != sha256_file(folder / "capture.wav")
        or native["artifact_sha256"] != sha256_file(root / native["artifact_path"])
        or sha256_file(root / registration["original_frequency_registration"])
        != registration["original_frequency_registration_sha256"]
    ):
        raise ValueError("Frozen method or exact native reception identity differs")
    reference_path = root / "experiments" / DIRECTORIES[0] / "resonance-frequency-results-001.json"
    reference = None
    if index:
        reference = json.loads(reference_path.read_text())
        reference_folder = reference_path.parent
        prior_native_path = reference_folder / "hardware-recapture-results-001.json"
        prior_native = json.loads(prior_native_path.read_text())
        if (
            reference["source_sha256"] != sha256_file(reference_folder / "playback.wav")
            or reference["registration_sha256"] != sha256_file(registration_path)
            or reference["native_results_sha256"] != sha256_file(prior_native_path)
            or prior_native["capture_sha256"] != sha256_file(reference_folder / "capture.wav")
            or prior_native["artifact_sha256"] != sha256_file(root / prior_native["artifact_path"])
            or not reference_audio_supported(reference, registration)
        ):
            raise ValueError("Verified prior native/audio identity differs or reference unusable")
    report = audio_report(audio_path, registration)
    report.update(
        registration_sha256=sha256_file(registration_path),
        native_results_sha256=sha256_file(native_path),
    )
    if not index:
        report["reference_frequency_supported"] = reference_audio_supported(report, registration)
    write_bytes(output, json_bytes(report))
    if index:
        comparison = compare_resonance_audio(reference, report, registration)
        comparison.update(
            analysis_version="native-bound-frozen-resonance-component-comparison-0.1",
            registration_sha256=sha256_file(registration_path),
            reference_audio_results_sha256=sha256_file(reference_path),
            candidate_audio_results_sha256=sha256_file(output),
            candidate_native_results_sha256=sha256_file(native_path),
            limits=registration["limits"],
        )
        write_bytes(comparison_path, json_bytes(comparison))
    if not report["passed"] or (not index and not report["reference_frequency_supported"]):
        raise ValueError("Frozen resonance tone measurement unusable; report retained")


if __name__ == "__main__":
    main()
