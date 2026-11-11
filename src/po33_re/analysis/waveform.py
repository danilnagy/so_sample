"""Amplitude-derived quarter clock, independent of measured zero crossings."""

import numpy as np


def amplitude_clock(values, rate, carrier_hz=7812.5, block_frames=500):
    if (
        not isinstance(values, np.ndarray)
        or values.ndim != 1
        or not np.issubdtype(values.dtype, np.floating)
        or not np.all(np.isfinite(values))
    ):
        raise ValueError("Finite one-dimensional waveform required")
    if type(block_frames) is not int or block_frames < 100 or len(values) < 4 * block_frames:
        raise ValueError("Insufficient waveform or clock window too short")
    if not np.isfinite(rate) or not np.isfinite(carrier_hz) or not 0 < carrier_hz < rate / 2:
        raise ValueError("Carrier must lie below Nyquist")
    centers, angles, strengths, means = [], [], [], []
    # Equal quadrature magnitudes imply (x^2 - A^2/2)^2 contains a fixed 4*f tone.
    for start in range(0, len(values) - block_frames + 1, block_frames):
        x = values[start : start + block_frames]
        square = x * x
        dc = float(np.mean(square))
        if dc < 1e-10:
            continue
        fourth = (square - dc) ** 2
        n = np.arange(start, start + block_frames)
        angle = 8 * np.pi * carrier_hz * n / rate
        basis = np.column_stack((np.ones(block_frames), np.cos(angle), np.sin(angle)))
        fitted = np.linalg.lstsq(basis, fourth, rcond=None)[0]
        component = complex(fitted[1], -fitted[2])
        centers.append(start + (block_frames - 1) / 2)
        angles.append(np.angle(component))
        strengths.append(float(abs(component) / max(float(np.std(fourth)), 1e-20)))
        means.append(dc)
    if len(centers) < 4:
        raise ValueError("Insufficient active clock windows")
    centers = np.asarray(centers)
    correction = np.unwrap(angles) / (8 * np.pi)
    return (
        centers,
        correction,
        {
            "clock_model": "amplitude fourth harmonic; no measured crossings",
            "carrier_hz": carrier_hz,
            "block_frames": block_frames,
            "windows": len(centers),
            "fourth_tone_to_std_min": float(np.min(strengths)),
            "fourth_tone_to_std_median": float(np.median(strengths)),
            "clock_drift_cycles": float(correction[-1] - correction[0]),
            "mean_square_min": float(np.min(means)),
            "phase_ambiguity": "one quarter cycle and whole-cycle acquisition",
        },
    )


def sample_quarters(values, rate, centers, correction, carrier_hz=7812.5):
    """Return sign samples on an amplitude-derived clock; no sign-run counts used."""
    if (
        len(centers) < 2
        or len(centers) != len(correction)
        or not np.all(np.isfinite(centers))
        or not np.all(np.isfinite(correction))
        or centers[0] < 0
        or centers[-1] > len(values) - 1
    ):
        raise ValueError("Invalid amplitude clock centers or corrections")
    clock_centers = centers * carrier_hz / rate + correction
    if np.any(np.diff(clock_centers) <= 0):
        raise ValueError("Amplitude clock is not monotonic")
    first = int(np.ceil(clock_centers[0] * 4 - 0.5))
    last = int(np.floor(clock_centers[-1] * 4 - 0.5))
    quarter_indices = np.arange(first, last + 1, dtype=np.int64)
    quarter_cycles = (quarter_indices + 0.5) / 4
    frames = np.interp(quarter_cycles, clock_centers, centers)
    before = np.floor(frames).astype(np.int64)
    after = np.minimum(before + 1, len(values) - 1)
    amplitudes = values[before] + (frames - before) * (values[after] - values[before])
    return quarter_indices, (amplitudes >= 0).astype(np.uint8), amplitudes
