"""Compare explicit serialized phase views under bounded lagged feedback models."""

import argparse
from pathlib import Path

import numpy as np

from po33_re.analysis.serialization import feedback_probe
from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def run(baseline_path, variant_path):
    baseline, variant = [load_artifact(p) for p in (baseline_path, variant_path)]
    if baseline.metadata["phase_convention"] != variant.metadata["phase_convention"]:
        raise ValueError("Different phase conventions")
    train, holdout = (20000, 36384), (50000, 66384)
    if (
        min(
            len(getattr(a, ch + "_symbols"))
            for a in (baseline, variant)
            for ch in ("left", "right")
        )
        < holdout[1] + 2
    ):
        raise ValueError("Insufficient symbols for fixed feedback windows")
    report = {
        "analysis_version": "serialized-feedback-probes-0.1",
        "inputs": [
            {
                "path": str(p),
                "artifact_sha256": sha256_file(p),
                "source_sha256": a.metadata["source_sha256"],
            }
            for p, a in zip((baseline_path, variant_path), (baseline, variant))
        ],
        "units": "candidate serialization of diagnostic phase values, not payload words",
        "training_span": list(train),
        "holdout_span": list(holdout),
        "window_units": "indices in each named view; no cross-view offset equivalence assumed",
        "packing": "first mapped label in least significant two bits",
        "phase_labels_rewritten": False,
        "payload_decoded": False,
        "views": [],
    }
    for view in ("raw_labels", "staggered_phase", "staggered_increments"):
        pairs = []
        for artifact in (baseline, variant):
            pair = []
            for ch in ("left", "right"):
                values = getattr(artifact, ch + "_symbols")
                if view != "raw_labels":
                    values = staggered_phases(values)
                if view == "staggered_increments":
                    values = phase_increments(values)
                pair.append(values)
            pairs.append(pair)
        training = [[s[train[0] : train[1]] for s in pair] for pair in pairs]
        heldout = [[s[holdout[0] : holdout[1]] for s in pair] for pair in pairs]
        details = {
            "view": view,
            "original_window_changed_fractions": [
                float(np.mean(a != b)) for a, b in zip(training[0], training[1])
            ],
            "probes": [],
        }
        for layout in ("left", "right", "stereo_symbols", "stereo_bytes"):
            for width in (1, 2, 4, 8):
                for endian in ("little", "big") if width > 1 else ("little",):
                    details["probes"].append(
                        feedback_probe(*training, *heldout, layout, width, endian)
                    )
        report["views"].append(details)
    report["total_candidates_tested"] = sum(
        p["candidates_tested"] for v in report["views"] for p in v["probes"]
    )
    report["limits"] = [
        "Same label permutation is used on both channels; independent channel mappings untested.",
        "No search for arbitrary bit offsets, variable-length coding or nonlinear feedback.",
        "Best candidate is chosen on training only; ties use enumeration order.",
        "Packing retains only full groups within explicitly chosen analysis windows.",
        "Low matching fractions reject localization by these transforms, not all state coding.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("variant", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    validate_outputs([args.out], [args.baseline, args.variant], args.force)
    write_bytes(args.out, json_bytes(run(args.baseline, args.variant)), args.force)


if __name__ == "__main__":
    main()
