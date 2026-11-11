"""Inspect copy growth and tail reuse without counting constant carrier as content."""

import argparse
from pathlib import Path

import numpy as np

from po33_re.analysis.alignment import equality_runs
from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def terminal_boundary(labels):
    increments = phase_increments(staggered_phases(labels))
    nonzero = np.flatnonzero(increments)
    if not len(nonzero):
        raise ValueError("No nonconstant transport content")
    last = int(nonzero[-1])
    return {
        "last_nonzero_increment_index": last,
        "terminal_zero_increment_span": [last + 1, len(increments)],
        "terminal_zero_increment_count": len(increments) - last - 1,
        "complete_label_count": len(labels),
        "final_raw_label": int(labels[-1]),
    }


def run(tone_path, copy1_path, before_path, after_path):
    paths = [tone_path, copy1_path, before_path, after_path]
    artifacts = [load_artifact(p) for p in paths]
    if len({a.metadata["phase_convention"] for a in artifacts}) != 1:
        raise ValueError("Different phase conventions")
    report = {
        "analysis_version": "copy-tail-structure-0.1",
        "selection": "Post-observation diagnostic; no preregistered endpoint interpretation",
        "inputs": [
            {
                "role": role,
                "path": str(p),
                "source_sha256": a.metadata["source_sha256"],
                "artifact_sha256": sha256_file(p),
            }
            for role, p, a in zip(
                ("tone8", "copy1", "clean_before", "clean_after"), paths, artifacts
            )
        ],
        "tail_probe_source_start": 177121,
        "diagnostic_shift_range_inclusive": [-128, 128],
        "channels": {},
        "payload_decoded": False,
    }
    for ch in ("left", "right"):
        arrays = [getattr(v, ch + "_symbols") for v in artifacts]
        boundaries = [terminal_boundary(x) for x in arrays]
        detail = {
            "terminal_boundaries": dict(
                zip(("tone8", "copy1", "clean_before", "clean_after"), boundaries)
            ),
            "copy1_last_transition_displacement": boundaries[1]["last_nonzero_increment_index"]
            - boundaries[0]["last_nonzero_increment_index"],
            "copy2_last_transition_displacement": boundaries[3]["last_nonzero_increment_index"]
            - boundaries[2]["last_nonzero_increment_index"],
            "tail_reuse_probes": {},
        }
        for view, transform in (
            ("raw", lambda x: x),
            ("staggered_phase", staggered_phases),
            ("increment", lambda x: phase_increments(staggered_phases(x))),
        ):
            a, b = [transform(x) for x in arrays[2:]]
            records = []
            for shift in range(-128, 129):
                # Retain all runs, then exclude single-valued runs explicitly. A long
                # carrier suffix cannot serve as evidence for reused metadata.
                runs = equality_runs(a, b, shift, 177121, limit=len(a))["longest_runs"]
                varied = [r for r in runs if len(r["distinct_values"]) > 1]
                records.append(
                    {
                        "shift": shift,
                        "longest_varied_run": varied[0] if varied else None,
                        "longest_any_run": runs[0] if runs else None,
                    }
                )
            best = max(
                records,
                key=lambda r: (
                    r["longest_varied_run"]["matching_values"] if r["longest_varied_run"] else 0
                ),
            )
            detail["tail_reuse_probes"][view] = {
                "best_varied_run": best,
                "at_zero_shift": records[128],
                "at_complete_count_growth_shift": records[128 + len(arrays[3]) - len(arrays[2])],
                "at_transition_growth_shift": records[
                    128 + detail["copy2_last_transition_displacement"]
                ],
            }
        report["channels"][ch] = detail
    report["limits"] = [
        "The last nonzero increment is an empirical waveform coordinate, not a parsed payload terminator.",
        "Zero increments are constant reassociated phase, not decoded zero data.",
        "Equal endpoint displacement suggests fixed growth but does not establish native record size.",
        "Finite offset search excludes constant runs from evidence for tail-content reuse.",
        "No array is shifted or trimmed in an artifact, encoder or restore.",
    ]
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("tone8", "copy1", "before", "after"):
        p.add_argument(name, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    paths = [args.tone8, args.copy1, args.before, args.after]
    validate_outputs([args.out], paths, False)
    write_bytes(args.out, json_bytes(run(*paths)))


if __name__ == "__main__":
    main()
