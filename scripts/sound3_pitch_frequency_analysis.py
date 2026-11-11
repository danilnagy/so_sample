"""Measure the registered pitch pair with one common unbiased frequency search."""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.fft import next_fast_len
from scipy.optimize import minimize_scalar
from scipy.signal import butter, sosfiltfilt

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.audio import PCM_SUBTYPES, load_pcm_wav
from scripts.prepare_generated_sound3_pitch_pair import DIRECTORIES, REGISTRATION
from scripts.swing_timing_analysis import measure_onsets


def fit_frequency(y, rate, parameters):
    low, high = parameters["frequency_search_hz"]
    size = next_fast_len(max(len(y), int(np.ceil(rate / parameters["fft_grid_max_spacing_hz"]))))
    spectrum = abs(np.fft.rfft((y - np.mean(y)) * np.hanning(len(y)), n=size))
    frequencies = np.fft.rfftfreq(size, 1 / rate)
    indices = np.flatnonzero((frequencies >= low) & (frequencies <= high))
    peak = float(frequencies[indices[np.argmax(spectrum[indices])]])
    width = parameters["fft_peak_refine_halfwidth_hz"]
    left, right = max(low, peak - width), min(high, peak + width)
    t = (np.arange(len(y)) - (len(y) - 1) / 2) / rate

    def error(frequency):
        basis = np.column_stack(
            (np.cos(2 * np.pi * frequency * t), np.sin(2 * np.pi * frequency * t), np.ones(len(t)))
        )
        coefficients = np.linalg.lstsq(basis, y, rcond=None)[0]
        return float(np.mean((y - basis @ coefficients) ** 2)), coefficients

    result = minimize_scalar(
        lambda frequency: error(frequency)[0],
        bounds=(left, right),
        method="bounded",
        options={"xatol": 1e-6},
    )
    residual, coefficients = error(float(result.x))
    variance = float(np.var(y))
    explained = 1 - residual / variance if variance else 0
    return {
        "frequency_hz": float(result.x),
        "fft_peak_hz": peak,
        "explained_variance": explained,
        "fundamental_amplitude": float(np.hypot(coefficients[0], coefficients[1])),
        "fit_success": bool(
            result.success
            and low + 0.01 < result.x < high - 0.01
            and left + 0.01 < result.x < right - 0.01
            and explained >= parameters["minimum_fit_explained_variance"]
        ),
    }


def measure_channel(values, rate, parameters):
    onsets = measure_onsets(values, rate, parameters)
    center, width = parameters["center_frequency_hz"], parameters["half_bandwidth_hz"]
    filtered = sosfiltfilt(
        butter(3, [center - width, center + width], fs=rate, btype="bandpass", output="sos"), values
    )
    measurements = []
    for onset in onsets["measurements"]:
        fits, excluded = [], []
        for index, (begin, end) in enumerate(onset["regions_frames"]):
            left, right = [
                begin + round(offset * rate)
                for offset in parameters["steady_fit_window_after_onset_seconds"]
            ]
            if right > end or right > len(filtered):
                excluded.append(index)
                continue
            fits.append(
                dict(
                    fit_frequency(filtered[left:right], rate, parameters),
                    onset_index=index,
                    fit_span_frames=[left, right],
                )
            )
        usable = (
            len(fits) >= 2 * parameters["minimum_complete_cycles"] + 1
            and all(index in (0, len(onset["regions_frames"]) - 1) for index in excluded)
            and all(fit["fit_success"] for fit in fits)
        )
        measurements.append(
            {
                "threshold_peak_fraction": onset["threshold_peak_fraction"],
                "onsets_seconds": onset["onsets_seconds"],
                "loop_median_seconds": onset["loop_median_seconds"],
                "fits": fits,
                "excluded_short_regions": excluded,
                "median_frequency_hz": float(np.median([fit["frequency_hz"] for fit in fits]))
                if fits
                else None,
                "usable": usable,
            }
        )
    consistent = (
        onsets["thresholds_agree"]
        and onsets["all_alternating_gaps_consistent"]
        and onsets["all_loops_near_registered137_bpm"]
    )
    return {
        "measurements": measurements,
        "band_peak_rms": onsets["band_peak_rms"],
        "onset_consistency_passed": consistent,
        "passed": consistent and all(item["usable"] for item in measurements),
    }


def audio_report(path, registration):
    samples, info = load_pcm_wav(path)
    parameters = registration["frequency_method"]["parameters"]
    channels = {}
    for index, name in enumerate(("left", "right")):
        try:
            channels[name] = measure_channel(samples[:, index], info["sample_rate_hz"], parameters)
        except ValueError as exc:
            channels[name] = {"passed": False, "error": str(exc), "measurements": []}
    stereo = []
    for a, b in zip(channels["left"]["measurements"], channels["right"]["measurements"]):
        x, y = np.array(a["onsets_seconds"]), np.array(b["onsets_seconds"])
        stereo.append(
            len(x) == len(y)
            and len(x) > 0
            and float(np.max(abs(x - y))) <= parameters["stereo_onset_tolerance_seconds"]
        )
    clipping = 1 - 2 ** (1 - PCM_SUBTYPES[info["pcm_subtype"]])
    checks = {
        "all_channel_measurements_usable": all(channel["passed"] for channel in channels.values()),
        "independent_stereo_onsets_agree": len(stereo) == 3 and all(stereo),
        "no_full_scale_samples": bool(np.all(abs(samples) < clipping)),
    }
    return {
        "analysis_version": "common-search-pitch13-14-frequency-measurement-0.1",
        "hardware_verified": False,
        "source_sha256": sha256_file(path),
        **info,
        "duration_seconds": len(samples) / info["sample_rate_hz"],
        "peaks_per_channel": np.max(abs(samples), axis=0).tolist(),
        "parameters": parameters,
        "channels": channels,
        "checks": checks,
        "passed": all(checks.values()),
    }


def compare_frequency_reports(reference, candidate, parameters):
    if reference["parameters"] != parameters or candidate["parameters"] != parameters:
        raise ValueError("Frequency parameters differ from frozen registration")
    rows = []
    for channel in ("left", "right"):
        a, b = [report["channels"][channel]["measurements"] for report in (reference, candidate)]
        if len(a) != 3 or len(b) != 3:
            raise ValueError("Three usable registered thresholds required per channel")
        for fraction, x, y in zip(parameters["threshold_peak_fractions"], a, b):
            if x["threshold_peak_fraction"] != fraction or y["threshold_peak_fraction"] != fraction:
                raise ValueError("Threshold sequence differs from frozen registration")
            ratio = (
                y["median_frequency_hz"] / x["median_frequency_hz"]
                if x["median_frequency_hz"] and y["median_frequency_hz"]
                else None
            )
            loop_delta = y["loop_median_seconds"] - x["loop_median_seconds"]
            consistent = (
                reference["passed"]
                and candidate["passed"]
                and x["usable"]
                and y["usable"]
                and ratio is not None
                and abs(x["median_frequency_hz"] / parameters["reference_frequency_lead_hz"] - 1)
                <= parameters["reference_frequency_relative_tolerance"]
                and abs(loop_delta) <= parameters["unchanged_loop_seconds_tolerance"]
            )
            rows.append(
                {
                    "channel": channel,
                    "threshold_peak_fraction": fraction,
                    "frequency_ratio_candidate_to_reference": ratio,
                    "interval_cents": float(1200 * np.log2(ratio)) if ratio else None,
                    "loop_delta_seconds": loop_delta,
                    "comparison_consistent": consistent,
                    "increased_frequency_supported": consistent
                    and ratio > 1 + parameters["minimum_relative_frequency_increase"],
                    "one_semitone_ratio_supported": consistent
                    and abs(ratio / parameters["hypothesized_ratio_for_one_semitone"] - 1)
                    <= parameters["semitone_ratio_relative_tolerance"],
                }
            )
    return {
        "hardware_verified": False,
        "measurements": rows,
        "all_frequency_increases_supported": all(
            row["increased_frequency_supported"] for row in rows
        ),
        "all_one_semitone_ratios_supported": all(
            row["one_semitone_ratio_supported"] for row in rows
        ),
        "all_codes_scale_or_full_field_width_confirmed": False,
        "pitch_field_writer_enabled": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leg", choices=("reference", "candidate"), required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments" / DIRECTORIES[("reference", "candidate").index(args.leg)]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    path = directory / "playback.wav"
    output = directory / "pitch-frequency-results-001.json"
    validate_outputs([output], [registration_path, path], False)
    report = audio_report(path, registration)
    if args.leg == "reference":
        parameters = registration["frequency_method"]["parameters"]
        measurements = [
            item for channel in report["channels"].values() for item in channel["measurements"]
        ]
        report["checks"]["reference_frequency_near_registered_lead"] = len(
            measurements
        ) == 6 and all(
            item["median_frequency_hz"] is not None
            and abs(item["median_frequency_hz"] / parameters["reference_frequency_lead_hz"] - 1)
            <= parameters["reference_frequency_relative_tolerance"]
            for item in measurements
        )
        report["passed"] = all(report["checks"].values())
    report["registration_sha256"] = sha256_file(registration_path)
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Registered pitch audio consistency failed; report retained")


if __name__ == "__main__":
    main()
