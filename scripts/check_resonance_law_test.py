"""Check the resonance law test: exact reception, then the peak of every resonance code."""

import argparse
import hashlib
import json
from itertools import pairwise
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.filter_response_method import SETTINGS, harmonic_amplitudes, responses
from scripts.prepare_resonance_law_test import (
    DIRECTORY,
    PEAK_BAND_HZ,
    REGISTRATION,
    step_layout,
)

DECISION = "resonance-law-decision-001.json"
CYCLES = 2


def peaks(response, layout):
    """Per resonance code: median response, peak dB and peak frequency."""
    table = {}
    for code in sorted({c for ref, c in layout if not ref}):
        rows = [
            response[n]
            for n, (ref, c) in enumerate(layout)
            if not ref and c == code and not np.isnan(response[n]).any()
        ]
        if rows:
            median = np.median(rows, axis=0)
            index = int(np.argmax(median))
            table[code] = {
                "response_db": median.tolist(),
                "peak_db": float(median[index]),
                "peak_hz": float((index + 1) * SETTINGS["fundamental_hz"]),
            }
    return table


def evaluate(response, layout, table):
    reference = [
        float(np.median(np.abs(response[n])))
        for n, (ref, _) in enumerate(layout)
        if ref and not np.isnan(response[n]).any()
    ]
    ordered = [table[c]["peak_db"] for c in sorted(table)]
    strong = [v["peak_hz"] for v in table.values() if v["peak_db"] >= 3.0]
    return {
        "reference_median_abs_db": reference,
        "hypotheses": {
            "reference_consistent": bool(reference) and max(reference) <= 0.5,
            "peak_rises": all(b >= a - 0.5 for a, b in pairwise(ordered)),
            "strong_at_63": 63 in table
            and 0 in table
            and table[63]["peak_db"] - table[0]["peak_db"] >= 10.0,
            "peak_near_edge": all(PEAK_BAND_HZ[0] <= hz <= PEAK_BAND_HZ[1] for hz in strong),
        },
        "peaks": {
            str(c): {"peak_db": v["peak_db"], "peak_hz": v["peak_hz"]} for c, v in table.items()
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
    ):
        raise ValueError("Frozen method changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "resonance-measurements-001.json"
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
        "analysis_version": "resonance-law-native-check-0.1",
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
    layout = step_layout() * CYCLES
    labels = [63 if ref else -1 for ref, _ in layout]
    first, amplitudes = harmonic_amplitudes(playback, len(layout), SETTINGS)
    response = responses(amplitudes, labels, len(step_layout()))
    table = peaks(response, layout)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "resonance-law-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "step_amplitudes": [
                    None if np.isnan(row).any() else row.tolist() for row in amplitudes
                ],
                "per_code": {str(k): v for k, v in table.items()},
            }
        ),
    )
    result = evaluate(response, layout, table)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "resonance-law-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "measurements_sha256": sha256_file(measure_path),
                **result,
                "limits": registration["limits"],
            }
        ),
    )
    summary = {c: [round(v["peak_db"], 1), v["peak_hz"]] for c, v in result["peaks"].items()}
    print(json.dumps({"native": True, "hypotheses": result["hypotheses"], "peaks": summary}))


if __name__ == "__main__":
    main()
