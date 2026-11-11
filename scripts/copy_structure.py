"""Reproduce content reuse and slot-offset hypotheses from the first copied sound."""

import argparse
from pathlib import Path

import numpy as np

from po33_re.analysis.alignment import equality_runs
from po33_re.analysis.anchors import extend_anchor, find_anchor, packed_offsets
from po33_re.analysis.coding import phase_coordinates
from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def run(source_path, copy_path):
    source, copy = [load_artifact(p) for p in (source_path, copy_path)]
    if source.metadata["phase_convention"] != copy.metadata["phase_convention"]:
        raise ValueError("Different phase conventions")
    report = {
        "analysis_version": "copy-content-structure-0.1",
        "inputs": [
            {
                "path": str(p),
                "artifact_sha256": sha256_file(p),
                "source_sha256": a.metadata["source_sha256"],
            }
            for p, a in zip((source_path, copy_path), (source, copy))
        ],
        "selection": "Post-observation offsets and anchors, no artifact normalization",
        "channels": {},
        "payload_decoded": False,
    }
    for channel in ("left", "right"):
        a, b = [getattr(v, channel + "_symbols") for v in (source, copy)]
        n = min(len(a), len(b))
        ix = np.flatnonzero(a[:n] != b[:n])
        p, q = staggered_phases(a), staggered_phases(b)
        dp, dq = phase_increments(p), phase_increments(q)
        details = {
            "raw_counts": [len(a), len(b)],
            "count_increase": len(b) - len(a),
            "strict_first_change": int(ix[0]) if len(ix) else None,
            "strict_changed_shared_labels": len(ix),
            "raw_diagnostic_offset": equality_runs(a, b, -84, 50000),
            "increment_diagnostic_offset": equality_runs(dp, dq, -84, 50000),
            "offset_search": [],
            "anchors": [],
        }
        for shift in range(-128, 129):
            detail = equality_runs(dp, dq, shift, 50000, limit=1)
            details["offset_search"].append(
                {"shift": shift, "equal_fraction": detail["equal_fraction"]}
            )
        largest = details["increment_diagnostic_offset"]["longest_runs"][0]
        begin, end = largest["source_span"]
        target_begin, target_end = largest["target_span"]
        details["phase_offsets_in_largest_run"] = (
            np.unique((q[target_begin:target_end].astype(np.int16) - p[begin:end]) % 4)
            .astype(int)
            .tolist()
        )
        x, y = phase_coordinates(dp).ravel(), phase_coordinates(dq).ravel()
        xstreams, ystreams = packed_offsets(x), packed_offsets(y)
        for position in (50000, 60000, 100000, 150000, 170000):
            start = position * 2
            if start + 256 > len(x):
                raise ValueError("Insufficient source for fixed copy anchors")
            needle = x[start : start + 256]
            self_hits = find_anchor(needle, xstreams, len(x))
            hits = find_anchor(needle, ystreams, len(y))
            details["anchors"].append(
                {
                    "source_start_coordinate": start,
                    "source_hits": self_hits,
                    "target_hits": hits,
                    "source_unique": self_hits["positions"] == [start]
                    and not self_hits["more_than_limit"],
                    "extensions": [
                        extend_anchor(x, y, start, t, 256, maximum=len(x))
                        for t in hits["positions"]
                    ],
                }
            )
        report["channels"][channel] = details
    report["limits"] = [
        "Small count growth suggests content reuse but does not prove allocation pointers or physical storage sharing.",
        "Shared regions are transport coordinates, not a decoded native waveform.",
        "The84-value displacement and12-value-per-slot idea are observational hypotheses from different operations.",
        "No checksum, state field or safe edited restore is established.",
    ]
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("copy", type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    validate_outputs([args.out], [args.source, args.copy], False)
    write_bytes(args.out, json_bytes(run(args.source, args.copy)))


if __name__ == "__main__":
    main()
