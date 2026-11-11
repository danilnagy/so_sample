"""Inspect trim differences and bounded binary feedback hypotheses."""

import argparse
from pathlib import Path

import numpy as np

from po33_re.analysis.coding import berlekamp_massey, phase_coordinates, recurrence_errors
from po33_re.analysis.staggered import constant_runs, phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def difference_summary(a, b):
    shared = min(len(a), len(b))
    indices = np.flatnonzero(a[:shared] != b[:shared])
    return {
        "comparison_span": [0, shared],
        "changed_values": len(indices),
        "first_change": int(indices[0]) if len(indices) else None,
        "last_change": int(indices[-1]) if len(indices) else None,
    }


def run(before_path, after_path):
    before, after = [load_artifact(p) for p in (before_path, after_path)]
    if before.metadata["phase_convention"] != after.metadata["phase_convention"]:
        raise ValueError("Different phase conventions")
    report = {
        "analysis_version": "trim-structure-0.1",
        "inputs": [
            {
                "path": str(p),
                "artifact_sha256": sha256_file(p),
                "source_sha256": a.metadata["source_sha256"],
            }
            for p, a in zip((before_path, after_path), (before, after))
        ],
        "selection": "Post-observation windows; coding hypotheses, not native trim offsets",
        "recurrence_training_span": [177200, 178224],
        "recurrence_holdout_span": [178224, 178736],
        "binary_recurrence_degree_bound": 256,
        "channels": {},
        "payload_decoded": False,
    }
    for ch in ("left", "right"):
        raw_a, raw_b = [getattr(v, ch + "_symbols") for v in (before, after)]
        phase_a, phase_b = staggered_phases(raw_a), staggered_phases(raw_b)
        increment_a, increment_b = phase_increments(phase_a), phase_increments(phase_b)
        summaries = {}
        deltas = {}
        for name, a, b in (
            ("raw", raw_a, raw_b),
            ("staggered_phase", phase_a, phase_b),
            ("increment", increment_a, increment_b),
        ):
            n = min(len(a), len(b))
            if n < 178736:
                raise ValueError("Insufficient values for fixed recurrence windows")
            summaries[name] = difference_summary(a, b)
            delta = ((b[:n].astype(np.int16) - a[:n]) % 4).astype(np.uint8)
            if name == "staggered_phase":
                summaries[name]["constant_relative_phase_runs"] = constant_runs(delta)
            deltas[name + "_xor"] = a[:n] ^ b[:n]
            if name != "raw":
                deltas[name + "_mod4_difference"] = delta
        probes = []
        for name, delta in deltas.items():
            lanes = phase_coordinates(delta[177200:178736])
            for lane in (0, 1):
                bits = lanes[:, lane]
                fit = berlekamp_massey(bits[:1024], max_degree=256)
                errors = recurrence_errors(bits, fit["tap_lags"], 1024) if fit["complete"] else None
                probes.append(
                    {
                        "delta_view": name,
                        "coordinate": "high" if lane == 0 else "low",
                        "fit": fit,
                        "holdout_errors": errors,
                        "nontrivial_training": bool(np.any(bits[:1024])),
                        "supported": fit["complete"] and errors == 0 and bool(np.any(bits[:1024])),
                    }
                )
        report["channels"][ch] = {"strict_differences": summaries, "recurrence_probes": probes}
    report["limits"] = [
        "Every comparison is zero shift; shared analysis spans do not truncate saved artifacts.",
        "Phase-offset tails are coordinate relations, not decoded zero or native sample values.",
        "Recurrence tests cover only the named binary differences and degree<=256.",
        "Plaintext constancy inside the metadata tail is unverified; failure cannot exclude every scrambler.",
        "No checksum, codec, encryption claim or safe writable field follows from these probes.",
    ]
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    validate_outputs([args.out], [args.before, args.after], False)
    write_bytes(args.out, json_bytes(run(args.before, args.after)))


if __name__ == "__main__":
    main()
