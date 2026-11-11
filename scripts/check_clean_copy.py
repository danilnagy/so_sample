"""Evaluate the clean copy pair against the unchanged prior registration."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def array_hash(values):
    return hashlib.sha256(values.tobytes()).hexdigest()


def compare(a, b):
    shared = min(len(a), len(b))
    changed = np.flatnonzero(a[:shared] != b[:shared])
    return {
        "complete_counts": [len(a), len(b)],
        "count_increase": len(b) - len(a),
        "changed_shared_labels": len(changed),
        "strict_first_change": int(changed[0]) if len(changed) else None,
        "strict_last_change": int(changed[-1]) if len(changed) else None,
        "complete_arrays_equal": bool(np.array_equal(a, b)),
    }


def run(registration_path, protocol_deviation=None, earlier_after=None):
    reg = json.loads(registration_path.read_text(encoding="utf-8"))
    paths = [
        Path(reg[key])
        for key in ("reference_artifact", "expected_before_artifact", "expected_after_artifact")
    ]
    if sha256_file(paths[0]) != reg["reference_artifact_sha256"]:
        raise ValueError("Registered reference artifact hash differs")
    reference, before, after = [load_artifact(p) for p in paths]
    artifacts = [reference, before, after]
    if earlier_after:
        artifacts.append(load_artifact(earlier_after))
        paths.append(earlier_after)
    if len({a.metadata["phase_convention"] for a in artifacts}) != 1:
        raise ValueError("Different phase conventions")
    report = {
        "analysis_version": "clean-copy-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "inputs": [
            {
                "path": str(p),
                "artifact_sha256": sha256_file(p),
                "source_sha256": a.metadata["source_sha256"],
                "decoder_version": a.metadata["decoder_version"],
            }
            for p, a in zip(paths, artifacts)
        ],
        "protocol_status": "deviation_reported" if protocol_deviation else "no_deviation_reported",
        "reported_deviation": protocol_deviation,
        "channels": {},
        "anchors": [],
        "payload_decoded": False,
    }
    begin, end = reg["reference_prefix_span"]
    for ch in ("left", "right"):
        r, a, b = [getattr(v, ch + "_symbols") for v in artifacts[:3]]
        expected_hash = reg["reference_prefix_sha256"][ch]
        if end > len(r) or array_hash(r[begin:end]) != expected_hash:
            raise ValueError("Registered reference prefix differs")
        detail = compare(a, b)
        detail["before_reference_prefix_matches"] = (
            end <= len(a) and array_hash(a[begin:end]) == expected_hash
        )
        lo, hi = reg["growth_symbols_per_channel_range_inclusive"]
        detail["growth_range_matches"] = lo <= detail["count_increase"] <= hi
        detail["observed_window_matches"] = {
            name: detail["strict_first_change"] is not None
            and window["first_raw_change_window"][0]
            <= detail["strict_first_change"]
            < window["first_raw_change_window"][1]
            for name, window in reg["first_change_models"].items()
        }
        detail["reference_to_before"] = compare(r, a)
        if earlier_after:
            detail["earlier_deviated_after_to_clean_after"] = compare(
                getattr(artifacts[3], ch + "_symbols"), b
            )
        detail["incomplete_final_sign_intervals"] = {
            role: v.metadata["channels"][ch]["boundary_sign_intervals"][
                "incomplete_final_cycle_bits"
            ]
            for role, v in zip(
                ("reference", "before", "after", "earlier_deviated_after"), artifacts
            )
        }
        report["channels"][ch] = detail
    for prediction in reg["anchor_predictions"]:
        ch = prediction["channel"]
        r, a, b = [
            phase_increments(staggered_phases(getattr(v, ch + "_symbols"))) for v in artifacts[:3]
        ]
        begin, end = prediction["source_increment_span"]
        tb, te = prediction["expected_same_target_increment_span"]
        if end > len(r) or array_hash(r[begin:end]) != prediction["uint8_increment_array_sha256"]:
            raise ValueError("Registered reference anchor differs")
        report["anchors"].append(
            {
                **prediction,
                "before_same_position_matches": bool(np.array_equal(r[begin:end], a[tb:te])),
                "after_same_position_matches": bool(np.array_equal(r[begin:end], b[tb:te])),
            }
        )
    applicable = all(v["before_reference_prefix_matches"] for v in report["channels"].values())
    applicable &= all(v["before_same_position_matches"] for v in report["anchors"])
    report["absolute_position_models_applicable"] = applicable
    report["single_action_interpretation_eligible"] = applicable and not bool(protocol_deviation)
    report["model_results"] = {
        name: (
            "inapplicable"
            if not report["single_action_interpretation_eligible"]
            else "window_prediction_passed"
            if all(v["observed_window_matches"][name] for v in report["channels"].values())
            else "window_prediction_failed"
        )
        for name in reg["first_change_models"]
    }
    if "last_nonzero_increment_predictions" in reg:
        report["analysis_version"] = "clean-copy-check-0.2"
        report["terminal_predictions"] = {}
        before_boundary_matches = True
        for ch, prediction in reg["last_nonzero_increment_predictions"].items():
            indices = []
            for artifact in artifacts[:3]:
                increments = phase_increments(staggered_phases(getattr(artifact, ch + "_symbols")))
                nonzero = np.flatnonzero(increments)
                indices.append(int(nonzero[-1]) if len(nonzero) else None)
            if indices[0] != prediction["before_index"]:
                raise ValueError("Registered reference terminal boundary differs")
            if (
                prediction["expected_after_index"] - prediction["before_index"]
                != prediction["expected_displacement"]
            ):
                raise ValueError("Inconsistent registered terminal prediction")
            before_matches = indices[1] == prediction["before_index"]
            before_boundary_matches &= before_matches
            report["terminal_predictions"][ch] = {
                **prediction,
                "actual_before_index": indices[1],
                "actual_after_index": indices[2],
                "before_boundary_matches": before_matches,
                "after_boundary_matches": indices[2] == prediction["expected_after_index"],
                "actual_displacement": indices[2] - indices[1] if None not in indices[1:] else None,
            }
        eligible = report["single_action_interpretation_eligible"] and before_boundary_matches
        combined_result_key = (
            "record_size_hypothesis_result"
            if "record_size_hypothesis" in reg
            else "registered_prediction_set_result"
        )
        report[combined_result_key] = (
            "inapplicable"
            if not eligible
            else "predictions_passed"
            if report["model_results"].get("inline_slots") == "window_prediction_passed"
            and all(v["growth_range_matches"] for v in report["channels"].values())
            and all(v["after_same_position_matches"] for v in report["anchors"])
            and all(v["after_boundary_matches"] for v in report["terminal_predictions"].values())
            else "predictions_failed"
        )
    report["limits"] = [
        "Protocol eligibility relies on user report; this script cannot observe hardware actions.",
        "Fresh before-state applicability is checked before interpreting absolute position models.",
        "No shifts, phase rotations, rewritten arrays or adjusted prediction windows are used.",
        "Complete arrays and partial terminal intervals are reported separately.",
        "Earlier deviated capture remains observational even if its complete arrays equal clean after.",
        "A successful location prediction does not decode native fields, storage pointers or checksums.",
    ]
    if "terminal_predictions" in report:
        report["limits"].append(
            "Last nonzero increments are empirical transport boundaries, not parsed payload terminators."
        )
    if "return_reference_artifact" in reg:
        return_path = Path(reg["return_reference_artifact"])
        if sha256_file(return_path) != reg["return_reference_artifact_sha256"]:
            raise ValueError("Registered return reference artifact hash differs")
        original = load_artifact(return_path)
        if original.metadata["phase_convention"] != after.metadata["phase_convention"]:
            raise ValueError("Return reference uses a different phase convention")
        report["analysis_version"] = "clean-copy-check-0.3"
        report["return_reference"] = {
            "path": str(return_path),
            "artifact_sha256": sha256_file(return_path),
            "source_sha256": original.metadata["source_sha256"],
            "channels": {},
        }
        begin, end = reg["expected_return_prefix_span"]
        for ch in ("left", "right"):
            r, b = [getattr(v, ch + "_symbols") for v in (original, after)]
            expected_hash = reg["expected_return_prefix_sha256"][ch]
            if end > len(r) or array_hash(r[begin:end]) != expected_hash:
                raise ValueError("Registered return prefix differs")
            report["return_reference"]["channels"][ch] = {
                "expected_prefix_span": [begin, end],
                "expected_prefix_matches": end <= len(b)
                and array_hash(b[begin:end]) == expected_hash,
                "full_complete_array_comparison": compare(r, b),
            }
        matched = all(
            v["expected_prefix_matches"] for v in report["return_reference"]["channels"].values()
        )
        report["return_prediction_result"] = (
            "inapplicable"
            if not report["single_action_interpretation_eligible"]
            else "predictions_passed"
            if matched and report.get("registered_prediction_set_result") == "predictions_passed"
            else "predictions_failed"
        )
        report["limits"].append(
            "Matching the registered original prefix is separate from exact complete-array/count equality."
        )
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("registration", type=Path)
    p.add_argument("--protocol-deviation")
    p.add_argument("--earlier-after", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    reg = json.loads(args.registration.read_text(encoding="utf-8"))
    inputs = [args.registration] + [
        Path(reg[key])
        for key in ("reference_artifact", "expected_before_artifact", "expected_after_artifact")
    ]
    if args.earlier_after:
        inputs.append(args.earlier_after)
    if "return_reference_artifact" in reg:
        inputs.append(Path(reg["return_reference_artifact"]))
    validate_outputs([args.out], inputs, False)
    write_bytes(
        args.out,
        json_bytes(run(args.registration, args.protocol_deviation, args.earlier_after)),
    )


if __name__ == "__main__":
    main()
