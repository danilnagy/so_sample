"""Bounded hypothesis probes, not a payload decoder or proof of encryption."""

import itertools
from pathlib import Path

import numpy as np

from ..artifacts import sha256_file
from ..modem.symbols import SymbolArtifact, load_artifact, validate_symbols
from .clock import audio_clock_report


def phase_coordinates(symbols: np.ndarray) -> np.ndarray:
    validate_symbols(symbols)
    return np.column_stack((symbols >> 1, symbols & 1)).astype(np.uint8)


def validate_bits(bits: np.ndarray) -> None:
    if not isinstance(bits, np.ndarray) or bits.dtype != np.uint8 or bits.ndim != 1:
        raise ValueError("Expected one-dimensional uint8 sign coordinates")
    if np.any(bits > 1):
        raise ValueError("Sign coordinates must be 0 or 1")


def berlekamp_massey(bits: np.ndarray, max_degree: int | None = None) -> dict:
    """Fit a binary linear recurrence. Index n uses the listed past lags."""
    validate_bits(bits)
    if max_degree is not None and (type(max_degree) is not int or max_degree < 0):
        raise ValueError("Maximum recurrence degree must be a nonnegative integer")
    size = len(bits)
    connection = np.zeros(size + 1, dtype=np.uint8)
    previous = connection.copy()
    connection[0] = previous[0] = 1
    degree, shift = 0, 1
    for n in range(size):
        discrepancy = int(bits[n])
        if degree:
            discrepancy ^= int(np.dot(connection[1 : degree + 1], bits[n - degree : n][::-1])) & 1
        if discrepancy:
            saved = connection.copy()
            connection[shift:] ^= previous[: size + 1 - shift]
            if 2 * degree <= n:
                degree, previous, shift = n + 1 - degree, saved, 1
            else:
                shift += 1
        else:
            shift += 1
        if max_degree is not None and degree > max_degree:
            return {
                "complete": False,
                "degree_lower_bound": degree,
                "samples_consumed": n + 1,
                "samples_available": size,
                "taps": None,
            }
    return {
        "complete": True,
        "degree": degree,
        "samples_consumed": size,
        "samples_available": size,
        "tap_lags": (np.flatnonzero(connection[1 : degree + 1]) + 1).astype(int).tolist(),
    }


def recurrence_errors(bits: np.ndarray, tap_lags: list[int], start: int) -> int:
    validate_bits(bits)
    if type(start) is not int or not 0 <= start <= len(bits):
        raise ValueError("Invalid holdout start")
    if any(type(lag) is not int or lag <= 0 or lag > start for lag in tap_lags):
        raise ValueError("Recurrence lags must be positive and supported by preceding samples")
    predicted = np.zeros(len(bits) - start, dtype=np.uint8)
    for lag in tap_lags:
        predicted ^= bits[start - lag : len(bits) - lag]
    return int(np.count_nonzero(bits[start:] != predicted))


def recurrence_probe(
    bits: np.ndarray, train: int = 512, holdout: int = 512, bound: int = 32
) -> dict:
    if any(type(value) is not int or value <= 0 for value in (train, holdout)):
        raise ValueError("Training and holdout lengths must be positive integers")
    if type(bound) is not int or bound < 0:
        raise ValueError("Recurrence bound must be a nonnegative integer")
    if len(bits) < train + holdout:
        raise ValueError("Insufficient coordinates for training and independent holdout")
    fitted = berlekamp_massey(bits[:train])
    errors = recurrence_errors(bits[: train + holdout], fitted["tap_lags"], train)
    return {
        "training_bits": train,
        "holdout_bits": holdout,
        "fitted_degree": fitted["degree"],
        "holdout_errors": errors,
        "small_degree_bound": bound,
        "small_recurrence_supported": fitted["degree"] <= bound and errors == 0,
        "trivial_zero_difference": not bool(np.any(bits[: train + holdout])),
        "tap_lags": fitted["tap_lags"] if fitted["degree"] <= bound else None,
    }


def repeated_prefix(
    symbols: np.ndarray, window_start: int = 100, window_end: int = 8000, max_period: int = 1024
) -> dict:
    validate_symbols(symbols)
    if not 0 <= window_start < window_end <= len(symbols):
        raise ValueError("Invalid repeated-prefix search window")
    if type(max_period) is not int or not 0 < max_period < window_end - window_start:
        raise ValueError("Invalid maximum period")
    values = symbols[window_start:window_end]
    period = next(
        (p for p in range(1, max_period + 1) if np.array_equal(values[p:], values[:-p])), None
    )
    first_break = None
    if period:
        changes = np.flatnonzero(symbols[period:] != symbols[:-period])
        if len(changes):
            first_break = int(changes[0] + period)
    return {
        "search_window": [window_start, window_end],
        "max_period": max_period,
        "smallest_exact_period_symbols": period,
        "first_period_break_symbol": first_break,
        "interpretation": "Repetition evidence; not a verified pilot/payload boundary",
    }


def gf2_rank(rows: np.ndarray) -> int:
    if not isinstance(rows, np.ndarray) or rows.dtype != np.uint8 or rows.ndim != 2:
        raise ValueError("Expected two-dimensional binary uint8 rows")
    if np.any(rows > 1):
        raise ValueError("GF(2) rows contain values outside 0..1")
    basis = {}
    for row in np.packbits(rows, axis=1, bitorder="little"):
        value = int.from_bytes(row.tobytes(), "little")
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)


def difference_lanes(baseline: SymbolArtifact, variant: SymbolArtifact) -> np.ndarray:
    baseline.validate()
    variant.validate()
    if baseline.metadata["phase_convention"] != variant.metadata["phase_convention"]:
        raise ValueError("Different phase conventions cannot be pooled")
    count = min(
        len(baseline.left_symbols),
        len(baseline.right_symbols),
        len(variant.left_symbols),
        len(variant.right_symbols),
    )
    left = phase_coordinates(baseline.left_symbols[:count] ^ variant.left_symbols[:count])
    right = phase_coordinates(baseline.right_symbols[:count] ^ variant.right_symbols[:count])
    return np.column_stack((left, right))


def coding_report(
    baseline_path: Path,
    variant_paths: list[Path],
    window_start: int = 20000,
    audio_paths: list[Path] | None = None,
) -> dict:
    if type(window_start) is not int or window_start < 0:
        raise ValueError("Analysis window start must be a nonnegative symbol index")
    if audio_paths is not None and len(audio_paths) != len(variant_paths) + 1:
        raise ValueError("Audio captures must correspond to baseline then each variant")
    baseline = load_artifact(baseline_path)
    report = {
        "schema_version": 1,
        "analysis_version": "bounded-coding-probes-0.1",
        "baseline_artifact": str(baseline_path),
        "baseline_artifact_sha256": sha256_file(baseline_path),
        "source_capture_sha256": baseline.metadata["source_sha256"],
        "phase_convention": baseline.metadata["phase_convention"],
        "lane_order": ["left_high", "left_low", "right_high", "right_low"],
        "units": "absolute phase-sign coordinates, not verified protocol bits",
        "alignment": "strict zero shift; retained analysis windows explicitly recorded",
        "prefix_structure": {
            ch: repeated_prefix(getattr(baseline, ch + "_symbols")) for ch in ("left", "right")
        },
        "variants": [],
        "payload_decoded": False,
        "limits": [
            "Finite probes cannot establish absence of all coding.",
            "Random-looking results do not prove encryption or compression.",
            "No state fields or safe edits are inferred.",
        ],
    }
    for path in variant_paths:
        variant = load_artifact(path)
        lanes = difference_lanes(baseline, variant)
        if len(lanes) < window_start + 98304:
            raise ValueError("Insufficient shared span for fixed recurrence and rank windows")
        details = {
            "artifact": str(path),
            "artifact_sha256": sha256_file(path),
            "source_capture_sha256": variant.metadata["source_sha256"],
            "retained_shared_symbols": len(lanes),
            "window_start_symbol": window_start,
            "channel_lengths": {
                ch: {
                    "baseline": len(getattr(baseline, ch + "_symbols")),
                    "variant": len(getattr(variant, ch + "_symbols")),
                }
                for ch in ("left", "right")
            },
            "coordinate_lanes": {},
            "stereo_orderings": [],
            "prefix_structure": {
                ch: repeated_prefix(getattr(variant, ch + "_symbols")) for ch in ("left", "right")
            },
        }
        for lane, name in enumerate(report["lane_order"]):
            details["coordinate_lanes"][name] = recurrence_probe(
                lanes[window_start : window_start + 1024, lane]
            )
        for ordering in itertools.permutations(range(4)):
            bits = lanes[window_start : window_start + 256, ordering].ravel()
            details["stereo_orderings"].append(
                {"lane_indices": list(ordering), **recurrence_probe(bits)}
            )
        candidates = []
        checked = 0
        for stride in range(1, 33):
            for offset in range(stride):
                for lane in range(4):
                    bits = lanes[
                        window_start + offset : window_start + offset + stride * 1024 : stride, lane
                    ]
                    fitted = berlekamp_massey(bits[:512], max_degree=32)
                    checked += 1
                    if fitted["complete"]:
                        errors = recurrence_errors(bits, fitted["tap_lags"], 512)
                        candidates.append(
                            {
                                "lane": lane,
                                "stride": stride,
                                "offset": offset,
                                "degree": fitted["degree"],
                                "holdout_errors": errors,
                                "supported": errors == 0,
                            }
                        )
        details["decimated_lanes"] = {
            "max_stride": 32,
            "max_degree": 32,
            "training_bits": 512,
            "holdout_bits": 512,
            "tested_mappings": checked,
            "candidates": candidates,
        }
        widths = (24, 48, 96, 192, 384)
        rank_probes = []
        for label, selected in (("left", (0, 1)), ("right", (2, 3)), ("stereo", (0, 1, 2, 3))):
            bits = lanes[window_start:, selected].ravel()
            for width in widths:
                count = width + 128
                rows = bits[: width * count].reshape(count, width)
                rank_probes.append(
                    {"mapping": label, "word_bits": width, "rows": count, "rank": gf2_rank(rows)}
                )
        details["linear_rank_difference_probes"] = rank_probes
        report["variants"].append(details)
    if audio_paths is not None:
        report["clock_probes"] = []
        for artifact_path, audio_path in zip([baseline_path, *variant_paths], audio_paths):
            artifact = load_artifact(artifact_path)
            thresholds = {}
            for name in ("left", "right"):
                threshold = artifact.metadata["channels"][name].get("normalized_crossing_threshold")
                if not isinstance(threshold, (float, int)):
                    raise ValueError("Artifact lacks normalized crossing threshold for clock probe")  # noqa: TRY004 -- invalid provenance schema
                thresholds[name] = threshold
            clock = audio_clock_report(audio_path, thresholds)
            if clock["source_sha256"] != artifact.metadata["source_sha256"]:
                raise ValueError(f"Audio source hash does not match artifact: {audio_path}")
            report["clock_probes"].append(clock)
    return report
