"""Check whether adjacent copied records share a literal phase-value template."""

import argparse
from itertools import permutations
from pathlib import Path

import numpy as np

from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def run(artifact_path):
    artifact = load_artifact(artifact_path)
    report = {
        "analysis_version": "copy-record-template-0.1",
        "artifact_sha256": sha256_file(artifact_path),
        "source_sha256": artifact.metadata["source_sha256"],
        "selection": "Post-observation; candidate record boundaries are not parsed fields",
        "candidate_starts": [177090, 177091, 177092, 177093],
        "candidate_record_length": 40,
        "channels": {},
        "payload_decoded": False,
    }
    for ch in ("left", "right"):
        raw = getattr(artifact, ch + "_symbols")
        views = {
            "raw": raw,
            "staggered_phase": staggered_phases(raw),
            "increment": phase_increments(staggered_phases(raw)),
        }
        probes = []
        for view, values in views.items():
            for begin in report["candidate_starts"]:
                if begin + 80 > len(values):
                    raise ValueError("Insufficient values for fixed candidate record spans")
                a, b = values[begin : begin + 40], values[begin + 40 : begin + 80]
                results = []
                for perm in permutations(range(4)):
                    mapped = np.array(perm, dtype=np.uint8)[a]
                    results.append((int(np.count_nonzero(mapped == b)), perm))
                matches, perm = max(results, key=lambda r: r[0])
                probes.append(
                    {
                        "view": view,
                        "source_span": [begin, begin + 40],
                        "target_span": [begin + 40, begin + 80],
                        "literal_matching_values": int(np.count_nonzero(a == b)),
                        "best_permutation": list(perm),
                        "best_matching_values": matches,
                        "exact_template_matches": matches == 40,
                    }
                )
        report["channels"][ch] = probes
    report["limits"] = [
        "Short candidate windows cannot identify a codec or establish statistical significance.",
        "Failure rejects literal or fixed-permutation equality at these candidate boundaries only.",
        "Distinct slot identity, stream context or unresolved coding may distinguish copied records.",
        "No field offsets, payload bytes or editable restore are established.",
    ]
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact", type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    validate_outputs([args.out], [args.artifact], False)
    write_bytes(args.out, json_bytes(run(args.artifact)))


if __name__ == "__main__":
    main()
