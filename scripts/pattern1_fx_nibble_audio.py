"""Frozen first-tone comparison for two complementary first-byte effect probes."""

import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.signal import butter, sosfiltfilt

from po33_re.artifacts import sha256_file
from po33_re.audio import PCM_SUBTYPES, load_pcm_wav
from scripts.sound3_pitch_frequency_analysis import fit_frequency

PARAMETERS = {
    "band_hz": [150.0, 3500.0],
    "envelope_seconds": 0.005,
    "threshold_peak_fractions": [0.15, 0.25, 0.35],
    "anchor_peak_fraction": 0.005,
    "anchor_minimum_region_seconds": 0.02,
    "maximum_first_onset_anchor_delay_seconds": 0.025,
    "minimum_band_rms": 0.001,
    "minimum_region_seconds": 0.06,
    "minimum_leading_silence_seconds": 0.3,
    "first_onset_search_end_seconds": 5.0,
    "steady_fit_window_after_onset_seconds": [0.08, 0.14],
    "frequency_search_hz": [400.0, 3000.0],
    "fft_grid_max_spacing_hz": 0.25,
    "fft_peak_refine_halfwidth_hz": 1.0,
    "minimum_fit_explained_variance": 0.9,
    "maximum_threshold_frequency_relative_spread": 0.005,
    "stereo_frequency_relative_tolerance": 0.005,
    "stereo_onset_tolerance_seconds": 0.002,
    "octave_ratio_relative_tolerance": 0.01,
}


def channel_report(values, rate, parameters):
    if parameters != PARAMETERS:
        raise ValueError("First-tone method differs from frozen parameters")
    filtered = sosfiltfilt(
        butter(3, parameters["band_hz"], fs=rate, btype="bandpass", output="sos"), values
    )
    envelope = np.sqrt(
        np.maximum(
            uniform_filter1d(filtered**2, size=round(parameters["envelope_seconds"] * rate)), 0
        )
    )
    peak = float(np.max(envelope))
    if peak < parameters["minimum_band_rms"]:
        raise ValueError("First-tone band absent or below usable level")
    anchor_edges = np.diff(
        np.r_[0, envelope > parameters["anchor_peak_fraction"] * peak, 0].astype(np.int8)
    )
    anchors = [
        (int(a), int(b))
        for a, b in zip(np.flatnonzero(anchor_edges == 1), np.flatnonzero(anchor_edges == -1))
        if b - a >= parameters["anchor_minimum_region_seconds"] * rate
    ]
    if not anchors:
        raise ValueError("First-tone anchor absent")
    anchor_start = anchors[0][0]
    rows = []
    for fraction in parameters["threshold_peak_fractions"]:
        edges = np.diff(np.r_[0, envelope > fraction * peak, 0].astype(np.int8))
        regions = [
            (int(a), int(b))
            for a, b in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))
            if b - a >= parameters["minimum_region_seconds"] * rate
        ]
        if not regions:
            raise ValueError("No usable first tone region")
        begin, end = regions[0]
        left, right = [
            begin + round(offset * rate)
            for offset in parameters["steady_fit_window_after_onset_seconds"]
        ]
        usable_span = (
            begin / rate >= parameters["minimum_leading_silence_seconds"]
            and begin / rate <= parameters["first_onset_search_end_seconds"]
            and abs(begin - anchor_start) / rate
            <= parameters["maximum_first_onset_anchor_delay_seconds"]
            and right <= end
        )
        fit = fit_frequency(filtered[left:right], rate, parameters) if usable_span else None
        rows.append(
            {
                "threshold_peak_fraction": fraction,
                "first_onset_seconds": begin / rate,
                "fit_span_frames": [left, right],
                "fit": fit,
                "usable": usable_span and fit["fit_success"],
            }
        )
    frequencies = [row["fit"]["frequency_hz"] for row in rows if row["usable"]]
    agree = (
        len(frequencies) == 3
        and np.ptp(frequencies) / np.median(frequencies)
        <= parameters["maximum_threshold_frequency_relative_spread"]
    )
    return {"measurements": rows, "passed": bool(agree)}


def audio_report(path, parameters):
    if parameters != PARAMETERS:
        raise ValueError("First-tone method differs from frozen parameters")
    samples, info = load_pcm_wav(path)
    channels = {}
    for index, name in enumerate(("left", "right")):
        try:
            channels[name] = channel_report(samples[:, index], info["sample_rate_hz"], parameters)
        except ValueError as exc:
            channels[name] = {"passed": False, "error": str(exc), "measurements": []}
    stereo = []
    for left, right in zip(channels["left"]["measurements"], channels["right"]["measurements"]):
        stereo.append(
            bool(
                left["usable"]
                and right["usable"]
                and abs(left["first_onset_seconds"] - right["first_onset_seconds"])
                <= parameters["stereo_onset_tolerance_seconds"]
                and abs(left["fit"]["frequency_hz"] / right["fit"]["frequency_hz"] - 1)
                <= parameters["stereo_frequency_relative_tolerance"]
            )
        )
    clipping = 1 - 2 ** (1 - PCM_SUBTYPES[info["pcm_subtype"]])
    checks = {
        "both_channels_usable": all(item["passed"] for item in channels.values()),
        "all_three_stereo_thresholds_agree": len(stereo) == 3 and all(stereo),
        "no_full_scale_samples": bool(np.all(abs(samples) < clipping)),
    }
    return {
        "analysis_version": "fixed-first-tone-wide-search-FX-nibble-probe-0.1",
        "hardware_verified": False,
        "source_sha256": sha256_file(path),
        **info,
        "parameters": parameters,
        "channels": channels,
        "checks": checks,
        "passed": all(checks.values()),
    }


def compare_audio(a, b, parameters):
    if parameters != PARAMETERS or any(report["parameters"] != parameters for report in (a, b)):
        raise ValueError("First-tone method differs from frozen parameters")
    usable = a["passed"] and b["passed"]
    ratios = []
    if usable:
        for channel in ("left", "right"):
            rows = [report["channels"][channel]["measurements"] for report in (a, b)]
            if any(len(items) != 3 for items in rows):
                usable = False
                break
            for fraction, x, y in zip(parameters["threshold_peak_fractions"], *rows):
                if (
                    x["threshold_peak_fraction"] != fraction
                    or y["threshold_peak_fraction"] != fraction
                ):
                    raise ValueError("First-tone threshold sequence differs")
                if (
                    not x["usable"]
                    or not y["usable"]
                    or any(
                        not row["fit"]["fit_success"]
                        or not np.isfinite(row["fit"]["frequency_hz"])
                        or row["fit"]["frequency_hz"] <= 0
                        for row in (x, y)
                    )
                ):
                    usable = False
                    break
                ratios.append(x["fit"]["frequency_hz"] / y["fit"]["frequency_hz"])
    usable = bool(usable and len(ratios) == 6)
    tolerance = parameters["octave_ratio_relative_tolerance"]
    low = usable and all(abs(ratio / 2 - 1) <= tolerance for ratio in ratios)
    high = usable and all(abs(ratio / 0.5 - 1) <= tolerance for ratio in ratios)
    return {
        "hardware_verified": False,
        "comparison_usable": usable,
        "first_tone_ratios_A_over_B": ratios,
        "low_nibble_first_model_supported": low,
        "high_nibble_first_model_supported": high,
        "classification": "low_nibble_first"
        if low
        else "high_nibble_first"
        if high
        else "inconclusive",
        "general_per_step_FX_writer_enabled": False,
    }
