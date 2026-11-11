"""Measure a pinned repeated tone for swing research without assuming timing units."""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.signal import butter, sosfiltfilt

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.audio import load_pcm_wav


def measure_onsets(values, rate, parameters):
    if (
        type(rate) is not int
        or rate <= 0
        or not isinstance(values, np.ndarray)
        or values.ndim != 1
        or not np.all(np.isfinite(values))
        or len(values) < rate
    ):
        raise ValueError("At least one second of finite one-dimensional audio required")
    frequency = parameters["center_frequency_hz"]
    width = parameters["half_bandwidth_hz"]
    if not 0 < frequency - width < frequency + width < rate / 2:
        raise ValueError("Tone band must be inside audio Nyquist limits")
    filtered = sosfiltfilt(
        butter(3, [frequency - width, frequency + width], btype="bandpass", fs=rate, output="sos"),
        values,
    )
    envelope = np.sqrt(
        np.maximum(
            uniform_filter1d(filtered**2, size=round(parameters["envelope_seconds"] * rate)), 0
        )
    )
    peak = float(np.max(envelope))
    if peak < parameters["minimum_band_rms"]:
        raise ValueError("Registered tone is absent or below usable level")
    measurements = []
    for fraction in parameters["threshold_peak_fractions"]:
        edges = np.diff(np.r_[0, envelope > fraction * peak, 0].astype(np.int8))
        regions = [
            (int(begin), int(end))
            for begin, end in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))
            if end - begin >= parameters["minimum_region_seconds"] * rate
            and begin >= parameters["edge_margin_seconds"] * rate
            and end <= len(values) - parameters["edge_margin_seconds"] * rate
        ]
        onsets = np.array([begin / rate for begin, _ in regions])
        if len(onsets) < 7:
            raise ValueError("At least seven resolvable onsets (three complete cycles) required")
        gaps = np.diff(onsets)
        parity = [gaps[::2], gaps[1::2]]
        medians = np.array([np.median(group) for group in parity])
        short_index = int(np.argmin(medians))
        short, long = parity[short_index], parity[1 - short_index]
        loops = onsets[2:] - onsets[:-2]
        short_median, long_median = float(np.median(short)), float(np.median(long))
        loop_median = float(np.median(loops))
        residual = max(
            float(np.max(abs(short - short_median))), float(np.max(abs(long - long_median)))
        )
        measurements.append(
            {
                "threshold_peak_fraction": fraction,
                "threshold_rms": fraction * peak,
                "onsets_seconds": onsets.tolist(),
                "regions_frames": regions,
                "complete_nonoverlapping_cycles": (len(onsets) - 1) // 2,
                "short_gap_median_seconds": short_median,
                "long_gap_median_seconds": long_median,
                "loop_median_seconds": loop_median,
                "maximum_gap_residual_seconds": residual,
                "alternating_gaps_consistent": residual
                <= parameters["maximum_gap_residual_seconds"],
                "loop_near_registered137_bpm": abs(loop_median - parameters["nominal_loop_seconds"])
                <= parameters["loop_tolerance_seconds"],
            }
        )
    short_values = [item["short_gap_median_seconds"] for item in measurements]
    long_values = [item["long_gap_median_seconds"] for item in measurements]
    return {
        "band_peak_rms": peak,
        "measurements": measurements,
        "thresholds_agree": bool(
            max(np.ptp(short_values), np.ptp(long_values))
            <= parameters["threshold_gap_spread_seconds"]
        ),
        "all_alternating_gaps_consistent": all(
            item["alternating_gaps_consistent"] for item in measurements
        ),
        "all_loops_near_registered137_bpm": all(
            item["loop_near_registered137_bpm"] for item in measurements
        ),
    }


def audio_report(path, registration):
    samples, info = load_pcm_wav(path)
    parameters = registration["parameters"]
    channels = {
        name: measure_onsets(samples[:, index], info["sample_rate_hz"], parameters)
        for index, name in enumerate(("left", "right"))
    }
    stereo = []
    for left, right in zip(channels["left"]["measurements"], channels["right"]["measurements"]):
        a, b = np.array(left["onsets_seconds"]), np.array(right["onsets_seconds"])
        stereo.append(
            len(a) == len(b)
            and float(np.max(abs(a - b))) <= parameters["stereo_onset_tolerance_seconds"]
        )
    checks = {
        "all_threshold_and_gap_checks": all(
            channel[key]
            for channel in channels.values()
            for key in (
                "thresholds_agree",
                "all_alternating_gaps_consistent",
                "all_loops_near_registered137_bpm",
            )
        ),
        "independent_stereo_onsets_agree": all(stereo),
        "capture_not_clipped": bool(np.all(abs(samples) < 1)),
    }
    return {
        "analysis_version": "registered-swing-tone-onsets-0.1",
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
            "Absolute onset times include filter and threshold delay; repeated interval comparison cancels common delay",
            "Tone selection comes from straight-control spectral exploration and is fixed before the swing6 capture",
            "No percentage or clock timing units inferred; manual observations remain separate",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments/swing-timing-measurement-registration-001.json"
    validate_outputs([args.out], [args.audio, registration_path], False)
    registration = json.loads(registration_path.read_text())
    report = audio_report(args.audio, registration)
    report["registration_sha256"] = sha256_file(registration_path)
    write_bytes(args.out, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Registered onset consistency checks failed; report retained")


if __name__ == "__main__":
    main()
