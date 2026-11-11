"""Measure ordinary sample playback; this does not demodulate backup audio."""

from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.signal import periodogram

from ..artifacts import sha256_file
from ..audio import load_pcm_wav


def measure_tone(values, rate):
    if (
        not isinstance(values, np.ndarray)
        or values.ndim != 1
        or not np.issubdtype(values.dtype, np.floating)
        or not np.all(np.isfinite(values))
    ):
        raise ValueError("Finite one-dimensional audio required")
    if type(rate) is not int or rate <= 0 or len(values) < round(0.2 * rate):
        raise ValueError("At least 200 ms of audio required")
    hop = max(1, round(0.01 * rate))
    count = len(values) // hop
    rms = np.sqrt(np.mean(values[: count * hop].reshape(count, hop) ** 2, axis=1))
    noise = float(np.quantile(rms, 0.2))
    threshold = max(8 * noise, 0.1 * float(np.max(rms)), 1e-5)
    active = rms >= threshold
    edges = np.diff(np.r_[0, active, 0].astype(np.int8))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    if not len(starts):
        raise ValueError("No sustained sound above activity threshold")
    longest = int(np.argmax(ends - starts))
    begin, end = int(starts[longest] * hop), int(ends[longest] * hop)
    if end - begin < round(0.1 * rate):
        raise ValueError("Longest active region is shorter than 100 ms")
    margin = min(round(0.05 * rate), (end - begin) // 8)
    fit_begin, fit_end = begin + margin, end - margin
    x = values[fit_begin:fit_end]
    t = (np.arange(len(x)) - (len(x) - 1) / 2) / rate
    frequencies, power = periodogram(x, rate, window="hann", nfft=1 << (len(x) - 1).bit_length())
    eligible = (frequencies >= 20) & (frequencies < min(8000, rate / 2))
    if not np.any(eligible):
        raise ValueError("No usable spectral bins")
    peak = int(np.flatnonzero(eligible)[np.argmax(power[eligible])])
    frequency = float(frequencies[peak])
    spacing = rate / (2 ** (len(x) - 1).bit_length())

    def fit(f):
        basis = np.column_stack(
            (np.cos(2 * np.pi * f * t), np.sin(2 * np.pi * f * t), np.ones(len(x)))
        )
        coeff = np.linalg.lstsq(basis, x, rcond=None)[0]
        residual = x - basis @ coeff
        return float(np.mean(residual**2)), coeff

    optimized = minimize_scalar(
        lambda f: fit(f)[0],
        bounds=(max(20, frequency - spacing), min(rate / 2, frequency + spacing)),
        method="bounded",
        options={"xatol": 1e-7},
    )
    if not optimized.success:
        raise ValueError("Tone frequency fit failed")
    frequency = float(optimized.x)
    error, coeff = fit(frequency)
    variance = float(np.var(x))
    return {
        "envelope_window_frames": hop,
        "activity_threshold_rms": threshold,
        "low_quantile_rms": noise,
        "audible_span_frames": [begin, end],
        "audible_span_seconds": [begin / rate, end / rate],
        "audible_duration_seconds": (end - begin) / rate,
        "frequency_fit_span_frames": [fit_begin, fit_end],
        "dominant_frequency_hz": frequency,
        "fundamental_amplitude": float(np.hypot(coeff[0], coeff[1])),
        "single_sine_explained_variance": 1 - error / variance if variance else None,
        "single_sine_residual_rms": float(np.sqrt(error)),
        "activity_regions": len(starts),
        "duration_resolution_seconds": hop / rate,
    }


def playback_report(path: Path, source_frequency=375.0):
    if not np.isfinite(source_frequency) or source_frequency <= 0:
        raise ValueError("Positive finite comparison frequency required")
    samples, info = load_pcm_wav(path)
    report = {
        "analysis_version": "ordinary-tone-playback-0.1",
        "path": str(path),
        "source_sha256": sha256_file(path),
        **info,
        "channels": {},
    }
    for i, channel in enumerate(("left", "right")):
        result = measure_tone(samples[:, i], info["sample_rate_hz"])
        ratio = result["dominant_frequency_hz"] / source_frequency
        result["comparison_to_input"] = {
            "input_frequency_hz": source_frequency,
            "playback_frequency_ratio": ratio,
            "pitch_difference_semitones": float(12 * np.log2(ratio)),
        }
        report["channels"][channel] = result
    report["limits"] = [
        "Measured duration is audible playback duration at the triggered melodic note, not native stored sample length.",
        "Input/playback pitch difference can reflect note transposition or existing parameter settings; exact button actions unknown.",
        "Envelope threshold and 10 ms bins determine reported sound boundaries.",
        "Single-sine residual includes noise, harmonics, modulation and processing; it is not a codec identification.",
        "No payload or native sample-rate mapping is inferred.",
    ]
    return report
