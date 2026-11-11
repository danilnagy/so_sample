"""Measure transport segmentation and channel relationships without decoding payload."""

import argparse
from itertools import combinations, product
from pathlib import Path

import numpy as np

from po33_re.analysis.coding import phase_coordinates
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def mapped_coordinates(bits, start, end, mapping):
    swap, high_lag, low_lag, mask = mapping
    return np.column_stack(
        (
            bits[start + high_lag : end + high_lag, int(swap)] ^ (mask >> 1),
            bits[start + low_lag : end + low_lag, 1 - int(swap)] ^ (mask & 1),
        )
    )


def coordinate_mapping_probe(a, b, train_start=1000000, holdout_start=1800000, size=4096):
    """Search a fixed late window, then test the selected mapping independently."""
    x, y = phase_coordinates(a), phase_coordinates(b)
    candidates = []
    for swap, high_lag, low_lag, mask in product(
        (False, True), range(-2, 3), range(-2, 3), range(4)
    ):
        mapping = (swap, high_lag, low_lag, mask)
        score = int(
            np.count_nonzero(
                np.all(
                    x[train_start : train_start + size]
                    == mapped_coordinates(y, train_start, train_start + size, mapping),
                    axis=1,
                )
            )
        )
        candidates.append((score, mapping))
    score = max(s for s, _ in candidates)
    winners = [m for s, m in candidates if s == score]
    mapping = winners[0]
    count = min(len(x), len(y))
    start, end = 2, count - 2
    changed = np.flatnonzero(
        np.any(x[start:end] != mapped_coordinates(y, start, end, mapping), axis=1)
    )
    return {
        "candidate_count": len(candidates),
        "training_span": [train_start, train_start + size],
        "training_matching_symbols": score,
        "tied_best_candidates": len(winners),
        "mapping": {
            "swap_coordinates": mapping[0],
            "high_lag": mapping[1],
            "low_lag": mapping[2],
            "xor_mask_high_low": mapping[3],
        },
        "holdout_span": [holdout_start, holdout_start + size],
        "holdout_matching_symbols": int(
            np.count_nonzero(
                np.all(
                    x[holdout_start : holdout_start + size]
                    == mapped_coordinates(y, holdout_start, holdout_start + size, mapping),
                    axis=1,
                )
            )
        ),
        "mapped_diagnostic_span": [start, end],
        "mapped_changed_symbols": len(changed),
        "mapped_first_change": int(changed[0] + start) if len(changed) else None,
        "mapped_last_change": int(changed[-1] + start) if len(changed) else None,
        "mapped_exact_suffix_symbols": end - int(changed[-1] + start) - 1
        if len(changed)
        else end - start,
        "interpretation": "Diagnostic mapping only; no artifact rewritten, no payload interpretation",
    }


def change_summary(a, b):
    count = min(len(a), len(b))
    changed = np.flatnonzero(a[:count] != b[:count])
    return {
        "shared_symbols": count,
        "lengths": [len(a), len(b)],
        "changed_symbols": len(changed),
        "first_change": int(changed[0]) if len(changed) else None,
        "last_change": int(changed[-1]) if len(changed) else None,
        "unchanged_suffix_symbols": count - int(changed[-1]) - 1 if len(changed) else count,
    }


def run(paths):
    artifacts = [load_artifact(path) for path in paths]
    if len({a.metadata["phase_convention"] for a in artifacts}) != 1:
        raise ValueError("Different phase conventions")
    if (
        min(len(getattr(a, ch + "_symbols")) for a in artifacts for ch in ("left", "right"))
        < 1900000
    ):
        raise ValueError("Fixed framing windows require at least 1900000 symbols per channel")
    report = {
        "analysis_version": "framing-probes-0.1",
        "inputs": [
            {
                "path": str(p),
                "artifact_sha256": sha256_file(p),
                "source_sha256": a.metadata["source_sha256"],
            }
            for p, a in zip(paths, artifacts)
        ],
        "units": "absolute phase labels/sign coordinates, not verified payload bits",
        "alignment_applied": False,
        "payload_decoded": False,
        "pairwise": [],
        "channel_probes": [],
    }
    for i, j in combinations(range(len(artifacts)), 2):
        pair = {"input_indices": [i, j], "channels": {}}
        for ch in ("left", "right"):
            a, b = (getattr(artifacts[k], ch + "_symbols") for k in (i, j))
            summary = change_summary(a, b)
            summary["coordinate_mapping_probe"] = coordinate_mapping_probe(a, b)
            count = min(len(a), len(b))
            summary["density_windows"] = [
                {
                    "span": [start, min(start + 8192, count)],
                    "changed": int(
                        np.count_nonzero(a[start : start + 8192] != b[start : start + 8192])
                    ),
                }
                for start in range(0, count - 8192 + 1, 8192)
            ]
            pair["channels"][ch] = summary
        report["pairwise"].append(pair)
    for index, artifact in enumerate(artifacts):
        lanes = np.column_stack(
            (
                phase_coordinates(artifact.left_symbols[:1900000]),
                phase_coordinates(artifact.right_symbols[:1900000]),
            )
        )
        for start in (100, 20000, 100000, 200000, 1000000, 1800000):
            size = 4096
            relationships = []
            # Signed lag is diagnostic only: compare lane B at start+lag with lane A.
            for a, b in combinations(range(4), 2):
                candidates = []
                for lag in range(-64, 65):
                    matches = int(
                        np.count_nonzero(
                            lanes[start : start + size, a]
                            == lanes[start + lag : start + lag + size, b]
                        )
                    )
                    candidates.append((max(matches, size - matches), lag, matches))
                score, lag, matches = max(candidates)
                relationships.append(
                    {
                        "lanes": [a, b],
                        "best_lag": lag,
                        "matching_coordinates": matches,
                        "best_equal_or_inverted_fraction": score / size,
                        "exact_equal_or_inverted": score == size,
                    }
                )
            report["channel_probes"].append(
                {
                    "input_index": index,
                    "span": [start, start + size],
                    "lags_tested": [-64, 64],
                    "relationships": relationships,
                }
            )
    report["limits"] = [
        "Window boundaries are chosen analysis bins, not packet boundaries.",
        "Lag searches are finite diagnostics; stored artifacts are never shifted.",
        "Equality or density cannot identify a cipher, checksum or writable field.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if len(args.inputs) < 2:
        parser.error("Provide at least two artifacts")
    validate_outputs([args.out], args.inputs, args.force)
    write_bytes(args.out, json_bytes(run(args.inputs)), args.force)


if __name__ == "__main__":
    main()
