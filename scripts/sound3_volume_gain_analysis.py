"""Measure fixed-tone amplitude and pitch for the registered volume ordering pair."""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.signal import butter, sosfiltfilt

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.audio import PCM_SUBTYPES, load_pcm_wav
from scripts.swing_timing_analysis import measure_onsets


def measure_channel(values, rate, parameters):
    onsets = measure_onsets(values, rate, parameters)
    center, width = parameters["center_frequency_hz"], parameters["half_bandwidth_hz"]
    filtered = sosfiltfilt(
        butter(3, [center - width, center + width], btype="bandpass", fs=rate, output="sos"), values
    )
    low = center * (1 - parameters["frequency_search_relative_halfwidth"])
    high = center * (1 + parameters["frequency_search_relative_halfwidth"])
    measurements = []
    for measurement in onsets["measurements"]:
        fits, excluded = [], []
        for index, (begin, end) in enumerate(measurement["regions_frames"]):
            left, right = [
                begin + round(offset * rate)
                for offset in parameters["steady_fit_window_after_onset_seconds"]
            ]
            if right > end or right > len(filtered):
                excluded.append(index)
                continue
            y = filtered[left:right]
            t = (np.arange(len(y)) - (len(y) - 1) / 2) / rate

            def fit(frequency, t=t, y=y):
                basis = np.column_stack(
                    (
                        np.cos(2 * np.pi * frequency * t),
                        np.sin(2 * np.pi * frequency * t),
                        np.ones(len(t)),
                    )
                )
                coefficients = np.linalg.lstsq(basis, y, rcond=None)[0]
                return float(np.mean((y - basis @ coefficients) ** 2)), coefficients

            optimized = minimize_scalar(
                lambda frequency: fit(frequency)[0],
                bounds=(low, high),
                method="bounded",
                options={"xatol": 1e-6},
            )
            error, coefficients = fit(float(optimized.x))
            variance = float(np.var(y))
            explained = 1 - error / variance if variance else 0
            fits.append(
                {
                    "onset_index": index,
                    "fit_span_frames": [left, right],
                    "frequency_hz": float(optimized.x),
                    "fundamental_amplitude": float(np.hypot(coefficients[0], coefficients[1])),
                    "explained_variance": explained,
                    "fit_success": bool(
                        optimized.success
                        and low + 0.01 < optimized.x < high - 0.01
                        and explained >= parameters["minimum_fit_explained_variance"]
                    ),
                }
            )
        enough = len(fits) >= 2 * parameters["minimum_complete_cycles"] + 1
        exclusions_at_edges = all(
            index in (0, len(measurement["regions_frames"]) - 1) for index in excluded
        )
        measurements.append(
            {
                "threshold_peak_fraction": measurement["threshold_peak_fraction"],
                "onsets_seconds": measurement["onsets_seconds"],
                "loop_median_seconds": measurement["loop_median_seconds"],
                "short_gap_median_seconds": measurement["short_gap_median_seconds"],
                "long_gap_median_seconds": measurement["long_gap_median_seconds"],
                "steady_tone_fits": fits,
                "excluded_short_regions": excluded,
                "median_amplitude": float(
                    np.median([item["fundamental_amplitude"] for item in fits])
                )
                if fits
                else None,
                "median_frequency_hz": float(np.median([item["frequency_hz"] for item in fits]))
                if fits
                else None,
                "usable": enough
                and exclusions_at_edges
                and all(item["fit_success"] for item in fits),
            }
        )
    consistent = (
        onsets["thresholds_agree"]
        and onsets["all_alternating_gaps_consistent"]
        and onsets["all_loops_near_registered137_bpm"]
    )
    return {
        "band_peak_rms": onsets["band_peak_rms"],
        "measurements": measurements,
        "onset_consistency_passed": consistent,
        "all_thresholds_usable": all(item["usable"] for item in measurements),
        "passed": consistent and all(item["usable"] for item in measurements),
    }


def audio_report(path, registration):
    samples, info = load_pcm_wav(path)
    parameters = registration["parameters"]
    channels = {
        name: measure_channel(samples[:, index], info["sample_rate_hz"], parameters)
        for index, name in enumerate(("left", "right"))
    }
    agreement = []
    for a, b in zip(channels["left"]["measurements"], channels["right"]["measurements"]):
        x, y = np.array(a["onsets_seconds"]), np.array(b["onsets_seconds"])
        agreement.append(
            len(x) == len(y)
            and float(np.max(abs(x - y))) <= parameters["stereo_onset_tolerance_seconds"]
        )
    clipping_threshold = 1 - 2 ** (1 - PCM_SUBTYPES[info["pcm_subtype"]])
    checks = {
        "all_channel_measurements_usable": all(channel["passed"] for channel in channels.values()),
        "independent_stereo_onsets_agree": all(agreement),
        "no_full_scale_samples": bool(np.all(abs(samples) < clipping_threshold)),
    }
    return {
        "analysis_version": "registered-volume-pair-tone-amplitude-measurement-0.1",
        "hardware_verified": False,
        "source_sha256": sha256_file(path),
        **info,
        "duration_seconds": len(samples) / info["sample_rate_hz"],
        "peaks_per_channel": np.max(abs(samples), axis=0).tolist(),
        "parameters": parameters,
        "channels": channels,
        "checks": checks,
        "passed": all(checks.values()),
        "limits": [
            "Steady sine amplitude is measured from the same repeated tone,not overall mix RMS",
            "Fixed band,fit window and thresholds are registered before pair audio; missing/unclear tone remains unevaluated",
            "No linear,dB or percent gain law assumed; pitch and loop consistency required",
        ],
    }


def compare_reports(reference, candidate, registration):
    parameters = registration["parameters"]
    if reference["parameters"] != parameters or candidate["parameters"] != parameters:
        raise ValueError("Gain parameters differ from frozen method registration")
    rows = []
    for channel in ("left", "right"):
        a, b = [report["channels"][channel]["measurements"] for report in (reference, candidate)]
        if len(a) != 3 or len(b) != 3:
            raise ValueError("All three registered thresholds required per channel")
        for fraction, x, y in zip(parameters["threshold_peak_fractions"], a, b):
            if x["threshold_peak_fraction"] != fraction or y["threshold_peak_fraction"] != fraction:
                raise ValueError("Gain threshold sequence differs from registration")
            ratio = (
                y["median_amplitude"] / x["median_amplitude"]
                if x["median_amplitude"] and y["median_amplitude"]
                else None
            )
            pitch_delta = (
                y["median_frequency_hz"] / x["median_frequency_hz"] - 1
                if x["median_frequency_hz"] and y["median_frequency_hz"]
                else None
            )
            loop_delta = y["loop_median_seconds"] - x["loop_median_seconds"]
            consistent = (
                reference["passed"]
                and candidate["passed"]
                and x["usable"]
                and y["usable"]
                and pitch_delta is not None
                and abs(pitch_delta) <= parameters["unchanged_pitch_relative_tolerance"]
                and abs(loop_delta) <= parameters["unchanged_loop_seconds_tolerance"]
            )
            rows.append(
                {
                    "channel": channel,
                    "threshold_peak_fraction": fraction,
                    "amplitude_ratio_candidate_to_reference": ratio,
                    "relative_frequency_delta": pitch_delta,
                    "loop_delta_seconds": loop_delta,
                    "comparison_consistent": consistent,
                    "contiguous_order_gain_direction_supported": consistent
                    and ratio is not None
                    and ratio < 1 - parameters["minimum_relative_amplitude_difference"],
                    "alternative_order_gain_direction_supported": consistent
                    and ratio is not None
                    and ratio > 1 + parameters["minimum_relative_amplitude_difference"],
                }
            )
    return {
        "hardware_verified": False,
        "measurements": rows,
        "all_contiguous_order_gain_directions_supported": all(
            row["contiguous_order_gain_direction_supported"] for row in rows
        ),
        "all_alternative_order_gain_directions_supported": all(
            row["alternative_order_gain_direction_supported"] for row in rows
        ),
        "gain_curve_or_numeric_UI_scale_confirmed": False,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    registration_path = root / "experiments/sound3-volume18-gain-method-registration-001.json"
    validate_outputs([args.out], [args.audio, registration_path], False)
    registration = json.loads(registration_path.read_text())
    report = audio_report(args.audio, registration)
    report["registration_sha256"] = sha256_file(registration_path)
    write_bytes(args.out, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Registered gain audio consistency failed; report retained")


if __name__ == "__main__":
    main()
