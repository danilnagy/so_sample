"""Bounded structure probes for an empty state and its first recorded sound."""

import argparse
from pathlib import Path

import numpy as np

from po33_re.analysis.anchors import find_anchor, packed_offsets
from po33_re.analysis.coding import phase_coordinates
from po33_re.analysis.periodicity import lag_runs, lag_similarity
from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def run(baseline_path, tone_path):
    baseline, tone = [load_artifact(p) for p in (baseline_path, tone_path)]
    if baseline.metadata["phase_convention"] != tone.metadata["phase_convention"]:
        raise ValueError("Different phase conventions")
    report = {
        "analysis_version": "minimal-one-tone-0.1",
        "inputs": [
            {
                "path": str(p),
                "artifact_sha256": sha256_file(p),
                "source_sha256": a.metadata["source_sha256"],
            }
            for p, a in zip((baseline_path, tone_path), (baseline, tone))
        ],
        "channels": {},
        "payload_decoded": False,
        "alignment_applied": False,
    }
    for channel in ("left", "right"):
        raw_a, raw_b = [getattr(a, channel + "_symbols") for a in (baseline, tone)]
        n = min(len(raw_a), len(raw_b))
        changed = np.flatnonzero(raw_a[:n] != raw_b[:n])
        details = {
            "raw_counts": [len(raw_a), len(raw_b)],
            "growth_symbols": len(raw_b) - len(raw_a),
            "first_change": int(changed[0]) if len(changed) else None,
            "last_change_in_shared_span": int(changed[-1]) if len(changed) else None,
            "changed_shared_symbols": len(changed),
            "views": [],
            "old_suffix_anchors": [],
            "suffix_displacements": [],
        }
        for view in ("raw_labels", "staggered_phase", "staggered_increments"):
            x = raw_b if view == "raw_labels" else staggered_phases(raw_b)
            if view == "staggered_increments":
                x = phase_increments(x)
            windows = []
            for start in range(45000, len(x) - 8192, 4096):
                scores = lag_similarity(x[start : start + 8192], 2048)
                lag = int(np.argmax(scores)) + 1
                windows.append(
                    {
                        "span": [start, start + 8192],
                        "best_lag": lag,
                        "equal_fraction": float(scores[lag - 1]),
                    }
                )
            details["views"].append(
                {
                    "view": view,
                    "search_window_frames": 8192,
                    "window_stride_values": 4096,
                    "lag_range": [1, 2048],
                    "top_similarity_windows": sorted(
                        windows, key=lambda w: w["equal_fraction"], reverse=True
                    )[:8],
                    "longest_lag520_runs_after45000": lag_runs(x, 520, window_start=45000, limit=3),
                }
            )
        a, b = [phase_increments(staggered_phases(x)) for x in (raw_a, raw_b)]
        target_bits = phase_coordinates(b).ravel()
        streams = packed_offsets(target_bits)
        for start in (42000, 43000, 43400, 44000, 44500):
            if start + 128 > len(a):
                raise ValueError("Baseline too short for fixed suffix anchors")
            needle = phase_coordinates(a[start : start + 128]).ravel()
            details["old_suffix_anchors"].append(
                {
                    "source_increment_start": start,
                    "anchor_coordinates": 256,
                    "matches": find_anchor(needle, streams, len(target_bits)),
                }
            )
        growth = len(b) - len(a)
        for shift in range(growth - 4, growth + 5):
            count = min(len(a), len(b) - shift)
            changes = np.flatnonzero(a[:count] != b[shift : shift + count])
            suffix = count - int(changes[-1]) - 1 if len(changes) else count
            values = a[count - suffix : count]
            details["suffix_displacements"].append(
                {
                    "shift_increments": shift,
                    "shared_count": count,
                    "equal_suffix_values": suffix,
                    "suffix_distinct_values": np.unique(values).astype(int).tolist(),
                }
            )
        report["channels"][channel] = details
    report["limits"] = [
        "Windows and anchors chosen after observing first divergence; not preregistered fields.",
        "No expected codec, native sample duration or internal sampling rate assumed.",
        "A constant terminal suffix across multiple shifts cannot establish meaningful insertion alignment.",
        "No long tone-period correlation in these views does not exclude other modulation/state decoding.",
    ]
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path)
    p.add_argument("tone", type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    validate_outputs([args.out], [args.baseline, args.tone], False)
    write_bytes(args.out, json_bytes(run(args.baseline, args.tone)))


if __name__ == "__main__":
    main()
