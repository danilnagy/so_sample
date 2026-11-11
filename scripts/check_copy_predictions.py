"""Evaluate registered copy windows without ignoring protocol deviations."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def run(registration_path, target_path, deviation):
    reg = json.loads(registration_path.read_text(encoding="utf-8"))
    source_path = Path(reg["source_artifact"])
    if sha256_file(source_path) != reg["source_artifact_sha256"]:
        raise ValueError("Preregistered source artifact hash differs")
    source, target = [load_artifact(p) for p in (source_path, target_path)]
    if source.metadata["phase_convention"] != target.metadata["phase_convention"]:
        raise ValueError("Different phase conventions")
    report = {
        "analysis_version": "registered-copy-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "source_artifact_sha256": sha256_file(source_path),
        "target_artifact_sha256": sha256_file(target_path),
        "target_capture_sha256": target.metadata["source_sha256"],
        "protocol_status": "deviated_user_reported" if deviation else "no_deviation_supplied",
        "reported_deviation": deviation,
        "causal_validation_eligible": not bool(deviation),
        "channels": {},
        "anchors": [],
        "limits": [
            "Matching windows do not establish native offsets or writable fields.",
            "When protocol differs, report observational matches only; do not confirm or causally reject models.",
            "Absence of a deviation argument is not independent hardware verification.",
        ],
    }
    for ch in ("left", "right"):
        a, b = [getattr(v, ch + "_symbols") for v in (source, target)]
        n = min(len(a), len(b))
        ix = np.flatnonzero(a[:n] != b[:n])
        first = int(ix[0]) if len(ix) else None
        detail = {
            "source_count": len(a),
            "actual_count": len(b),
            "count_increase": len(b) - len(a),
            "strict_first_change": first,
            "changed_shared_labels": len(ix),
            "observed_window_matches": {},
        }
        for key in ("front_table", "inline_slots"):
            lo, hi = reg["hypotheses"][key]["first_raw_change_window"]
            detail["observed_window_matches"][key] = first is not None and lo <= first < hi
        lo, hi = reg["hypotheses"]["small_metadata_growth"]["complete_symbols_range_inclusive"]
        detail["observed_small_count_range_matches"] = lo <= len(b) <= hi
        report["channels"][ch] = detail
    for prediction in reg["anchor_predictions"]:
        ch = prediction["channel"]
        a, b = [
            phase_increments(staggered_phases(getattr(v, ch + "_symbols")))
            for v in (source, target)
        ]
        begin, end = prediction["source_increment_span"]
        tb, te = prediction["expected_same_target_increment_span"]
        if (
            hashlib.sha256(a[begin:end].tobytes()).hexdigest()
            != prediction["uint8_increment_array_sha256"]
        ):
            raise ValueError("Preregistered source anchor differs")
        report["anchors"].append(
            {
                **prediction,
                "observed_same_position_match": bool(np.array_equal(a[begin:end], b[tb:te])),
            }
        )
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("registration", type=Path)
    p.add_argument("target", type=Path)
    p.add_argument("--protocol-deviation")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    reg = json.loads(args.registration.read_text(encoding="utf-8"))
    validate_outputs(
        [args.out], [args.registration, args.target, Path(reg["source_artifact"])], False
    )
    write_bytes(args.out, json_bytes(run(args.registration, args.target, args.protocol_deviation)))


if __name__ == "__main__":
    main()
