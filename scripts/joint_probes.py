"""Register or check fixed predictions for the two-kick joint-state control."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.analysis.superposition import compare_prediction, predict_joint
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def view_values(artifact, channel, view):
    raw = getattr(artifact, channel + "_symbols")
    if view == "raw_labels":
        return raw
    phases = staggered_phases(raw)
    return phases if view == "staggered_phase" else phase_increments(phases)


def run(paths, joint_path=None, registration_path=None):
    artifacts = [load_artifact(p) for p in paths]
    joint = load_artifact(joint_path) if joint_path else None
    if (
        len({a.metadata["phase_convention"] for a in [*artifacts, *([joint] if joint else [])]})
        != 1
    ):
        raise ValueError("Different phase conventions")
    report = {
        "analysis_version": "fixed-joint-probes-0.1",
        "input_roles": ["empty", "step1", "step2"],
        "inputs": [
            {
                "path": str(p),
                "artifact_sha256": sha256_file(p),
                "source_sha256": a.metadata["source_sha256"],
            }
            for p, a in zip(paths, artifacts)
        ],
        "status": "comparison" if joint else "registered_before_joint_capture",
        "payload_decoded": False,
        "predictions": [],
        "limits": [
            "These fixed affine hypotheses require independent state edits; UI state may confound them.",
            "No shifting, fitting, label permutation or tail correction is applied.",
            "Failure rejects only these views/models, not every possible linear code.",
            "Array hashes are uint8 diagnostic values, not hashes of a verified state image.",
        ],
    }
    if joint:
        if registration_path is None:
            raise ValueError("Joint comparison requires its preregistration report")
        prior = json.loads(registration_path.read_text(encoding="utf-8"))
        if (
            prior["status"] != "registered_before_joint_capture"
            or prior["inputs"] != report["inputs"]
        ):
            raise ValueError("Preregistered source artifacts differ")
        report["registration_sha256"] = sha256_file(registration_path)
        report["joint"] = {
            "path": str(joint_path),
            "artifact_sha256": sha256_file(joint_path),
            "source_sha256": joint.metadata["source_sha256"],
        }
    for view in ("raw_labels", "staggered_phase", "staggered_increments"):
        for channel in ("left", "right"):
            arrays = [view_values(a, channel, view) for a in artifacts]
            for model in ("coordinate_xor", "add_mod4"):
                predicted = predict_joint(*arrays, model)
                detail = {
                    "view": view,
                    "channel": channel,
                    "model": model,
                    "source_lengths": [len(a) for a in arrays],
                    "predicted_count": len(predicted),
                    "predicted_uint8_array_sha256": hashlib.sha256(predicted.tobytes()).hexdigest(),
                }
                if joint:
                    if detail != prior["predictions"][len(report["predictions"])]:
                        raise ValueError("Prediction does not match preregistered values")
                    detail["comparison"] = compare_prediction(
                        predicted, view_values(joint, channel, view)
                    )
                report["predictions"].append(detail)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("empty", type=Path)
    parser.add_argument("step1", type=Path)
    parser.add_argument("step2", type=Path)
    parser.add_argument("--joint", type=Path)
    parser.add_argument("--registration", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    paths = [args.empty, args.step1, args.step2]
    validate_outputs(
        [args.out],
        [
            *paths,
            *([args.joint] if args.joint else []),
            *([args.registration] if args.registration else []),
        ],
        False,
    )
    write_bytes(args.out, json_bytes(run(paths, args.joint, args.registration)))


if __name__ == "__main__":
    main()
