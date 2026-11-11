"""Check local crossing counts against a tracked quarter-cycle grid."""

from pathlib import Path

import numpy as np

from ..artifacts import sha256_file
from ..audio import load_pcm_wav


def clock_grid_probe(
    values: np.ndarray,
    rate: int,
    threshold: float,
    carrier_hz: float = 7812.5,
    block_frames: int = 1000,
) -> dict:
    if not np.isfinite(threshold) or not 0 < threshold < 1:
        raise ValueError("Clock-probe threshold must be finite and in (0,1)")
    if not np.isfinite(carrier_hz) or not 0 < carrier_hz < rate / 2:
        raise ValueError("Clock-probe carrier must be finite and below Nyquist")
    if type(block_frames) is not int or block_frames <= 0:
        raise ValueError("Clock-probe block size must be positive")
    indices = np.flatnonzero(np.abs(values) >= threshold)
    if len(indices) < 2:
        raise ValueError("Clock probe requires signal above threshold")
    signs = values[indices] >= 0
    changes = np.flatnonzero(signs[1:] != signs[:-1]) + 1
    if len(changes) < 2:
        raise ValueError("Clock probe requires multiple physical zero crossings")
    before, after = indices[changes - 1], indices[changes]
    fractions = np.abs(values[before]) / (np.abs(values[before]) + np.abs(values[after]))
    times = before + fractions * (after - before)
    period = rate / (4 * carrier_hz)
    block_ids = np.floor(times / block_frames).astype(np.int64)
    origin_block = int(block_ids[0])
    relative = block_ids - origin_block
    phase_vectors = np.exp(2j * np.pi * times / period)
    sums = np.bincount(relative, weights=phase_vectors.real) + 1j * np.bincount(
        relative, weights=phase_vectors.imag
    )
    counts = np.bincount(relative)
    occupied = counts > 0
    phase = np.unwrap(np.angle(sums[occupied])) / (2 * np.pi)
    centers = (np.flatnonzero(occupied) + origin_block + 0.5) * block_frames
    tracked = np.interp(times, centers, phase)
    grid = np.rint(times / period - tracked).astype(np.int64)
    grid_counts = np.diff(grid)
    local_counts = np.rint(np.diff(times) / (rate / (4 * 7800))).astype(np.int64)
    mismatch = np.flatnonzero(grid_counts != local_counts)
    concentration = np.abs(sums[occupied]) / counts[occupied]
    return {
        "nominal_grid_carrier_hz": carrier_hz,
        "reference_local_carrier_hz": 7800,
        "threshold": threshold,
        "block_frames": block_frames,
        "physical_crossing_count": len(times),
        "interval_count": len(local_counts),
        "first_crossing_sample": float(times[0]),
        "last_crossing_sample": float(times[-1]),
        "phase_concentration_min": float(np.min(concentration)),
        "phase_concentration_median": float(np.median(concentration)),
        "blocks_below_0_7_concentration": int(np.count_nonzero(concentration < 0.7)),
        "clock_analysis_version": "quarter-grid-0.2",
        "tracked_quarter_phase_drift": float(phase[-1] - phase[0]),
        "grid_negative_intervals": int(np.count_nonzero(grid_counts < 0)),
        "local_minus_grid_total_quarters": int(np.sum(local_counts) - np.sum(grid_counts)),
        "interval_disagreements": len(mismatch),
        "first_disagreement_samples": times[mismatch[:32]].tolist(),
        "disagreement_list_limit": 32,
        "limits": [
            "Uses the same measured crossings but a different global clock estimate.",
            "Does not prove protocol framing, bit interpretation or device clock tolerance.",
            "Low concentration or rapid drift can invalidate this clock estimator.",
        ],
    }


def audio_clock_report(path: Path, thresholds: dict) -> dict:
    source_hash = sha256_file(path)
    samples, info = load_pcm_wav(path)
    channels = {
        name: clock_grid_probe(samples[:, index], info["sample_rate_hz"], thresholds[name])
        for index, name in enumerate(("left", "right"))
    }
    return {"capture": str(path), "source_sha256": source_hash, **info, "channels": channels}
