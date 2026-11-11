"""Reproduce reversible staggered-phase diagnostics; no payload export or restore."""

import argparse
from pathlib import Path

import numpy as np

from po33_re.analysis.coding import phase_coordinates, recurrence_probe
from po33_re.analysis.staggered import (
    constant_runs,
    phase_increments,
    restore_labels,
    staggered_phases,
)
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def changes(a, b):
    count = min(len(a), len(b))
    positions = np.flatnonzero(a[:count] != b[:count])
    return {
        "lengths": [len(a), len(b)],
        "shared_count": count,
        "changed_count": len(positions),
        "first_change": int(positions[0]) if len(positions) else None,
        "last_change": int(positions[-1]) if len(positions) else None,
    }


def run(paths):
    artifacts = [load_artifact(p) for p in paths]
    if len({a.metadata["phase_convention"] for a in artifacts}) != 1:
        raise ValueError("Different phase conventions")
    report = {
        "analysis_version": "staggered-phase-probes-0.1",
        "inputs": [
            {
                "path": str(p),
                "artifact_sha256": sha256_file(p),
                "source_sha256": a.metadata["source_sha256"],
            }
            for p, a in zip(paths, artifacts)
        ],
        "grouping": "cell[n] = (high[n+1], low[n]); circular indices 10=0,11=1,01=2,00=3",
        "increment": "increment[n] = (phase[n+1] - phase[n]) modulo 4",
        "units": "diagnostic phase cells and increments, not verified protocol bits",
        "original_artifacts_modified": False,
        "payload_decoded": False,
        "roundtrip_checks": [],
        "variants": [],
    }
    phases = []
    for i, artifact in enumerate(artifacts):
        channels = {}
        for ch in ("left", "right"):
            raw = getattr(artifact, ch + "_symbols")
            if len(raw) < 21026:
                raise ValueError("Fixed recurrence window requires at least 21026 labels")
            grouped = staggered_phases(raw)
            initial_high, final_low = int(raw[0] >> 1), int(raw[-1] & 1)
            increments = phase_increments(grouped)
            recovered = (
                (int(grouped[0]) + np.r_[0, np.cumsum(increments, dtype=np.int64)]) % 4
            ).astype(np.uint8)
            report["roundtrip_checks"].append(
                {
                    "input_index": i,
                    "channel": ch,
                    "labels": len(raw),
                    "phase_cells": len(grouped),
                    "increments": len(increments),
                    "initial_high": initial_high,
                    "final_low": final_low,
                    "initial_phase": int(grouped[0]),
                    "increments_inverse_exact": bool(np.array_equal(recovered, grouped)),
                    "original_labels_inverse_exact": bool(
                        np.array_equal(restore_labels(recovered, initial_high, final_low), raw)
                    ),
                }
            )
            channels[ch] = grouped
        phases.append(channels)
    for i in range(1, len(artifacts)):
        variant = {"input_indices": [0, i], "channels": {}}
        for ch in ("left", "right"):
            a, b = phases[0][ch], phases[i][ch]
            count = min(len(a), len(b))
            relative = ((b[:count].astype(np.int16) - a[:count]) % 4).astype(np.uint8)
            da, db = phase_increments(a), phase_increments(b)
            probes = []
            for mode in ("xor", "subtract_mod4"):
                x, y = da[20000:21024], db[20000:21024]
                difference = (
                    x ^ y if mode == "xor" else ((y.astype(np.int16) - x) % 4).astype(np.uint8)
                )
                probes.append(
                    {
                        "mode": mode,
                        "increment_span": [20000, 21024],
                        "coordinate_probes": [
                            recurrence_probe(lane) for lane in phase_coordinates(difference).T
                        ],
                    }
                )
            variant["channels"][ch] = {
                "phase_comparison": changes(a, b),
                "relative_phase_runs_minimum64": constant_runs(relative),
                "increment_comparison": changes(da, db),
                "recurrence_probes": probes,
            }
        report["variants"].append(variant)
    report["limits"] = [
        "Regrouping follows encoder component indices; it is not verified protocol framing.",
        "Phase-cell and increment indices differ from original absolute-label indices.",
        "A constant relative phase disappears from increments, but earlier differences persist.",
        "Boundary coordinates and initial phase must be retained for a lossless inverse.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if len(args.inputs) < 2:
        parser.error("Provide a baseline and at least one variant")
    validate_outputs([args.out], args.inputs, args.force)
    write_bytes(args.out, json_bytes(run(args.inputs)), args.force)


if __name__ == "__main__":
    main()
