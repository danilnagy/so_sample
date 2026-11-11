"""Check the no-lock test: exact reception, then whether code-0 steps hold the last lock."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.filter_response_method import SETTINGS, harmonic_amplitudes, responses
from scripts.prepare_no_lock_test import (
    CYCLES,
    DIRECTORY,
    REGISTRATION,
    held_pairs,
    step_plan,
)

DECISION = "no-lock-decision-001.json"
TOLERANCE_DB = 1.0


def difference(response, a, b):
    return float(np.median(np.abs(response[a] - response[b])))


def evaluate(response, steps_per_cycle):
    plan = step_plan()
    cycles = range(len(response) // steps_per_cycle)
    rows = []
    for zero, locked, parameter in held_pairs():
        held = [
            difference(response, c * steps_per_cycle + zero, c * steps_per_cycle + locked)
            for c in cycles
        ]
        off = [float(np.median(np.abs(response[c * steps_per_cycle + zero]))) for c in cycles]
        rows.append(
            {
                "step": list(plan[zero][:2]),
                "parameter": parameter,
                "held_from_step": list(plan[locked][:2]),
                "held_value": plan[locked][2 if parameter == "filter" else 3],
                "median_diff_from_lock_db": float(np.nanmedian(held)),
                "median_abs_vs_bypass_db": float(np.nanmedian(off)),
            }
        )
    filter_rows = [r for r in rows if r["parameter"] == "filter"]
    return {
        "pairs": rows,
        "hypotheses": {
            "zero_holds_last_lock": all(
                r["median_diff_from_lock_db"] <= TOLERANCE_DB for r in rows
            ),
            "zero_filter_is_off": all(
                r["median_abs_vs_bypass_db"] <= TOLERANCE_DB for r in filter_rows
            ),
        },
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / "scripts/filter_response_method.py")
        != registration["method_script_sha256"]
        or registration["method_settings"] != SETTINGS
        or registration["held_pairs"] != [list(p) for p in held_pairs()]
    ):
        raise ValueError("Frozen method or plan changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "no-lock-measurements-001.json"
    decision_path = root / "experiments" / DECISION
    validate_outputs(
        [native_path, measure_path, decision_path],
        [capture, playback, artifact_path, target_path],
        False,
    )
    if sha256_file(target_path) != registration["edited_artifact_sha256"]:
        raise ValueError("Registered target changed")
    artifact = load_artifact(artifact_path)
    capture_hash = sha256_file(capture)
    if artifact.metadata["source_sha256"] != capture_hash:
        raise ValueError("Analysis artifact is not from capture.wav")
    target = decode_artifact(load_artifact(target_path))
    actual = decode_artifact(artifact)
    checks = {
        "native_valid": encode_packets(actual.packets) == actual.encoded_body,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "no-lock-native-check-0.1",
        "hardware_verified": False,
        "passed": all(checks.values()),
        "checks": checks,
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": capture_hash,
        "artifact_sha256": sha256_file(artifact_path),
        "native_frame": frame_report(actual),
    }
    write_bytes(native_path, json_bytes(native))
    if not native["passed"]:
        print(json.dumps({"native": False, "checks": checks}, indent=2))
        raise ValueError("Native reception failed; report retained")
    plan = step_plan()
    labels = [63 if p == 1 and f == 63 else -1 for p, _, f, _ in plan] * CYCLES
    first, amplitudes = harmonic_amplitudes(playback, len(labels), SETTINGS)
    response = responses(amplitudes, labels, len(plan))
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "no-lock-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "step_amplitudes": [
                    None if np.isnan(row).any() else row.tolist() for row in amplitudes
                ],
            }
        ),
    )
    result = evaluate(response, len(plan))
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "no-lock-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "measurements_sha256": sha256_file(measure_path),
                **result,
                "limits": registration["limits"],
            }
        ),
    )
    print(
        json.dumps(
            {
                "native": True,
                "hypotheses": result["hypotheses"],
                "pairs": [
                    [
                        r["parameter"],
                        r["step"],
                        r["held_value"],
                        round(r["median_diff_from_lock_db"], 2),
                        round(r["median_abs_vs_bypass_db"], 2),
                    ]
                    for r in result["pairs"]
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
