"""Experimental absolute phase demodulation with explicit boundary accounting.

The algorithm derives phase labels from quarter-cycle sign runs. Acquisition is
an upstream-compatible candidate, not proof of protocol synchronization.
"""

from pathlib import Path

import numpy as np

from ..artifacts import sha256_file
from ..audio import load_pcm_wav
from .symbols import PHASE_CONVENTION, SCHEMA, SymbolArtifact

DECODER_VERSION = "sign-crossings-0.2"
DEFAULT_THRESHOLD = 10 / 32768
CARRIER_HZ = 7800


class DecodeFailure(RuntimeError):
    """Valid audio with no usable phase-symbol acquisition."""


def decode_channel(values: np.ndarray, rate: int, threshold: float) -> tuple[np.ndarray, dict]:
    indices = np.flatnonzero(np.abs(values) >= threshold)
    if len(indices) < 2:
        raise DecodeFailure("No signal crossings above the normalized threshold")
    signs = values[indices] >= 0
    changes = np.flatnonzero(signs[1:] != signs[:-1]) + 1
    before, after = indices[changes - 1], indices[changes]
    fractions = np.abs(values[before]) / (np.abs(values[before]) + np.abs(values[after]))
    crossings = before + fractions * (after - before)
    sides = signs[changes]
    # Approximate the initial negative transition at the first observed thresholded sample.
    # File time zero may precede the signal by seconds; it must not invent a negative run.
    initial_origin = bool(not signs[0])
    if initial_origin:
        crossings = np.r_[float(indices[0]), crossings]
        sides = np.r_[False, sides]
    if len(crossings) < 2:
        raise DecodeFailure("Insufficient zero crossings")
    interval_units = np.diff(crossings) / (rate / (CARRIER_HZ * 4))
    counts = np.rint(interval_units).astype(np.int64)
    if np.any(counts > CARRIER_HZ * 4):
        raise DecodeFailure("Crossing gap exceeds one second; refusing to invent a long sign run")
    bit_values = (~sides[1:]).astype(np.uint8)
    bits = np.repeat(bit_values, counts)
    sync_candidates = np.flatnonzero((bits[:-1] == 1) & (bits[1:] == 1))
    if not len(sync_candidates):
        raise DecodeFailure("No first-11 phase acquisition candidate")
    sync = int(sync_candidates[0])
    processed = np.r_[np.uint8(1), bits[sync + 2 :]]
    complete = len(processed) // 4
    groups = processed[: complete * 4].reshape(-1, 4)
    symbols = ((groups[:, 0] << 1) | groups[:, 1]).astype(np.uint8)
    if not len(symbols):
        raise DecodeFailure("No complete phase cycles after acquisition")
    residual = np.abs(interval_units - counts)
    positive = counts > 0
    start_interval = int(np.searchsorted(np.cumsum(counts), sync + 1))
    acquisition_sample = float(crossings[start_interval])
    report = {
        "symbol_count": len(symbols),
        "crossing_count": len(crossings),
        "normalized_crossing_threshold": threshold,
        "boundaries": {
            "first_crossing_sample": float(crossings[0]),
            "last_crossing_sample": float(crossings[-1]),
            "acquisition_candidate_sample": acquisition_sample,
            "acquisition_verified": False,
            "first_significant_sample": int(indices[0]),
            "last_significant_sample": int(indices[-1]),
        },
        "discarded_samples": {
            "before_first_crossing": float(crossings[0]),
            "after_last_crossing": float(len(values) - 1 - crossings[-1]),
            "note": "No amplitude-based trimming; no sign-run estimate outside crossing span.",
        },
        "boundary_sign_intervals": {
            "prefix_count_before_sync_pair": sync,
            "prefix_bits_hex": np.packbits(bits[:sync], bitorder="little").tobytes().hex(),
            "consumed_sync_pair": [1, 1],
            "reinserted_sign_interval": 1,
            "incomplete_final_cycle_bits": processed[complete * 4 :].tolist(),
            "zero_length_intervals": int(np.count_nonzero(~positive)),
        },
        "uncertainty": {
            "status": "experimental_unverified_phase_labels",
            "quarter_interval_residual_max": float(np.max(residual)),
            "quarter_interval_residual_p95": float(np.quantile(residual, 0.95)),
            "intervals_over_quarter_unit": int(np.count_nonzero(residual > 0.25)),
            "interval_count": len(residual),
            "fraction_over_quarter_unit": float(np.mean(residual > 0.25)),
            "clock_model": "nominal 7800 Hz carrier; no drift correction",
        },
        "initial_negative_origin_inserted": initial_origin,
        "initial_negative_origin_sample": float(indices[0]) if initial_origin else None,
        "initial_negative_origin_policy": "first thresholded sample; do not count leading silence",
    }
    return symbols, report


def decode_wav(path: Path, threshold: float = DEFAULT_THRESHOLD) -> SymbolArtifact:
    if not np.isfinite(threshold) or not 0 < threshold < 1:
        raise ValueError("Normalized threshold must be finite and between 0 and 1")
    source_hash = sha256_file(path)
    samples, info = load_pcm_wav(path)
    if info["sample_rate_hz"] < 2 * CARRIER_HZ:
        raise ValueError("Sample rate is too low for the nominal carrier")
    channels = {}
    streams = []
    for index, channel in enumerate(("left", "right")):
        try:
            symbols, report = decode_channel(samples[:, index], info["sample_rate_hz"], threshold)
        except DecodeFailure as exc:
            raise DecodeFailure(f"{channel}: {exc}") from exc
        streams.append(symbols)
        channels[channel] = report
    return SymbolArtifact(
        *streams,
        {
            "schema": SCHEMA,
            "schema_version": 1,
            "decoder_version": DECODER_VERSION,
            "phase_convention": PHASE_CONVENTION,
            "source_sha256": source_hash,
            "channel_order": ["left", "right"],
            **info,
            "channels": channels,
            "transformations": [
                "normalized integer PCM",
                "interpolated thresholded zero crossings",
                "rounded quarter-cycle sign intervals",
                "candidate first-11 acquisition",
                "first sign pair of each complete carrier cycle",
            ],
            "warnings": [
                "Phase labels are not verified protocol payload or device state.",
                "Noise outside the transfer may produce extra symbols.",
                "Acquisition and nominal clock require independent validation.",
            ],
            "hardware_verified": False,
        },
    )
