"""Check the parameter-only lock test: which value each unlocked note played."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.filter_response_method import SETTINGS, harmonic_amplitudes, responses
from scripts.prepare_param_only_test import (
    CYCLES,
    DIRECTORY,
    FLOOR_DB,
    MODELS,
    NOTE_FILTERS,
    REFERENCE_FILTERS,
    REGISTRATION,
    TOLERANCE_DB,
    UNLOCKED_STEPS,
    reference_step,
)

DECISION = "param-only-decision-001.json"
STEPS = 32


def difference(response, a, b, floor=FLOOR_DB):
    keep = (response[a] >= floor) | (response[b] >= floor)
    return float(np.median(np.abs(response[a][keep] - response[b][keep])))


def evaluate(response):
    cycles = range(len(response) // STEPS)
    rows, support = [], {}
    for name, values in MODELS.items():
        ok = True
        for step, value in zip(UNLOCKED_STEPS, values, strict=True):
            ref = 16 + reference_step(value) - 1
            diffs = [difference(response, c * STEPS + step - 1, c * STEPS + ref) for c in cycles]
            diff = float(np.nanmedian(diffs))
            rows.append({"model": name, "step": step, "value": value, "median_diff_db": diff})
            ok = ok and diff <= TOLERANCE_DB
        support[name] = ok
    supported = [name for name, ok in support.items() if ok]
    return {
        "comparisons": rows,
        "model_support": support,
        "classification": supported[0] if len(supported) == 1 else "other_or_inconclusive",
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
        or registration["models"] != MODELS
    ):
        raise ValueError("Frozen method or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "param-only-measurements-001.json"
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
        "analysis_version": "param-only-native-check-0.1",
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
    filters = NOTE_FILTERS + REFERENCE_FILTERS
    labels = [63 if f == 63 else -1 for f in filters] * CYCLES
    first, amplitudes = harmonic_amplitudes(playback, len(labels), SETTINGS)
    response = responses(amplitudes, labels, STEPS)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "param-only-measurements-0.1",
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
    result = evaluate(response)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "param-only-decision-0.1",
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
                "model_support": result["model_support"],
                "classification": result["classification"],
                "comparisons": [
                    [r["model"], r["step"], r["value"], round(r["median_diff_db"], 2)]
                    for r in result["comparisons"]
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
