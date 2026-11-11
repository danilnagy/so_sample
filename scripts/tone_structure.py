"""Reproduce tone-control period and displaced-suffix probes without normalizing artifacts."""

import argparse
from pathlib import Path

import numpy as np

from po33_re.analysis.periodicity import lag_runs, lag_similarity, smallest_period
from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def run(baseline_path, variant_path):
    a, b = [load_artifact(p) for p in (baseline_path, variant_path)]
    if a.metadata["phase_convention"] != b.metadata["phase_convention"]:
        raise ValueError("Different phase conventions")
    report = {
        "analysis_version": "tone-structure-0.1",
        "inputs": [
            {
                "path": str(p),
                "artifact_sha256": sha256_file(p),
                "source_sha256": v.metadata["source_sha256"],
            }
            for p, v in zip((baseline_path, variant_path), (a, b))
        ],
        "payload_decoded": False,
        "original_artifacts_normalized": False,
        "channels": {},
    }
    for channel in ("left", "right"):
        raw_a, raw_b = [getattr(v, channel + "_symbols") for v in (a, b)]
        n = min(len(raw_a), len(raw_b))
        changed = np.flatnonzero(raw_a[:n] != raw_b[:n])
        details = {
            "raw_lengths": [len(raw_a), len(raw_b)],
            "raw_first_change": int(changed[0]) if len(changed) else None,
            "raw_changed_shared_symbols": len(changed),
            "views": [],
            "displacement_probes": [],
        }
        for view in ("raw_labels", "staggered_phase", "staggered_increments"):
            values = [raw_a, raw_b]
            if view != "raw_labels":
                values = [staggered_phases(x) for x in values]
            if view == "staggered_increments":
                values = [phase_increments(x) for x in values]
            v = {"view": view, "period_lag_post_observation": 520, "captures": []}
            for name, x in zip(("baseline", "tone"), values):
                rows = []
                for start in range(16384, len(x) - 16384, 8192):
                    scores = lag_similarity(x[start : start + 16384])
                    lag = int(np.argmax(scores)) + 1
                    rows.append(
                        {
                            "span": [start, start + 16384],
                            "best_lag": lag,
                            "equal_fraction": float(scores[lag - 1]),
                        }
                    )
                runs = lag_runs(x, 520)
                begin, end = runs[0]["covered_value_span"]
                v["captures"].append(
                    {
                        "name": name,
                        "top_similarity_windows": sorted(
                            rows, key=lambda r: r["equal_fraction"], reverse=True
                        )[:8],
                        "longest_lag520_runs": runs,
                        "smallest_period_longest_covered_region": smallest_period(
                            x[begin:end], min(2048, end - begin - 1)
                        ),
                    }
                )
            details["views"].append(v)
        x, y = [phase_increments(staggered_phases(z)) for z in (raw_a, raw_b)]
        for displacement in range(100356, 100365):
            n = min(len(x), len(y) - displacement)
            differences = np.flatnonzero(x[:n] != y[displacement : displacement + n])
            details["displacement_probes"].append(
                {
                    "displacement_increments": displacement,
                    "baseline_comparison_span": [0, n],
                    "tone_comparison_span": [displacement, displacement + n],
                    "changed_count": len(differences),
                    "last_change": int(differences[-1]) if len(differences) else None,
                    "exact_suffix_increments": n - int(differences[-1]) - 1
                    if len(differences)
                    else n,
                    "late_span_baseline": [1500000, n],
                    "late_equal_fraction": float(
                        np.mean(x[1500000:n] == y[1500000 + displacement : displacement + n])
                    ),
                }
            )
        report["channels"][channel] = details
    report["limits"] = [
        "Period 520 and displacement range were chosen after inspecting this capture.",
        "Chosen windows/coordinate indices are not verified sample or packet offsets.",
        "Repeating regions also exist in baseline, so repetition is not uniquely identified as tone content.",
        "Neither 260 stereo bytes per putative period nor near-integer period count proves a frame format.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("variant", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    validate_outputs([args.out], [args.baseline, args.variant], False)
    write_bytes(args.out, json_bytes(run(args.baseline, args.variant)))


if __name__ == "__main__":
    main()
