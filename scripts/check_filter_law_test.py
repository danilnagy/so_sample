"""Check the filter law test: exact reception, then the response and edge of every code."""

import argparse
import hashlib
import json
from itertools import pairwise
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.globals import pattern_chain
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.filter_response_method import SETTINGS, classify, harmonic_amplitudes, responses
from scripts.prepare_filter_law_test import (
    DIRECTORY,
    FILTER_CODES,
    PATTERNS,
    REGISTRATION,
    step_codes,
)

DECISION = "filter-law-decision-001.json"
CYCLES = 2


def per_code(response, codes):
    table = {}
    for code in sorted(set(codes)):
        rows = [response[n] for n, c in enumerate(codes) if c == code]
        rows = [r for r in rows if not np.isnan(r).any()]
        if rows:
            median = np.median(rows, axis=0)
            table[code] = {"response_db": median.tolist(), **classify(median, SETTINGS)}
    return table


def monotonic(table, kind, tolerance):
    edges = [(c, v["edge_hz"]) for c, v in sorted(table.items()) if v["type"] == kind]
    edges = [(c, e) for c, e in edges if e is not None]
    return all(b[1] >= a[1] - tolerance for a, b in pairwise(edges)), edges


def evaluate(response, codes, table):
    bypass = [
        float(np.median(np.abs(response[n])))
        for n, c in enumerate(codes)
        if c == 63 and not np.isnan(response[n]).any()
    ]
    types = {c: v["type"] for c, v in table.items()}
    low_ok, low_edges = monotonic(table, "low_pass", SETTINGS["fundamental_hz"])
    high_ok, high_edges = monotonic(table, "high_pass", SETTINGS["fundamental_hz"])
    return {
        "bypass_median_abs_db": bypass,
        "hypotheses": {
            "reference_consistent": bool(bypass) and max(bypass) <= 0.5,
            "low_codes_low_pass": all(
                types.get(c) in ("low_pass", "flat", "silent") for c in range(1, 32)
            )
            and all(types.get(c) in ("low_pass", "silent") for c in range(1, 17)),
            "high_codes_high_pass": all(
                types.get(c) in ("high_pass", "flat", "silent") for c in range(32, 63)
            )
            and all(types.get(c) in ("high_pass", "silent") for c in range(47, 63)),
            "edges_monotonic": low_ok and high_ok,
        },
        "types": {str(c): t for c, t in types.items()},
        "low_pass_edges_hz": low_edges,
        "high_pass_edges_hz": high_edges,
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
    measure_path = folder / "filter-measurements-001.json"
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
        "planned_chain": pattern_chain(actual) == PATTERNS,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "filter-law-native-check-0.1",
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
    codes = step_codes() * CYCLES
    first, amplitudes = harmonic_amplitudes(playback, len(codes), SETTINGS)
    response = responses(amplitudes, codes, len(step_codes()))
    table = per_code(response, codes)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "filter-law-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "filter_codes_by_pattern": {str(k): v for k, v in FILTER_CODES.items()},
                "step_amplitudes": [
                    None if np.isnan(row).any() else row.tolist() for row in amplitudes
                ],
                "per_code": {str(k): v for k, v in table.items()},
            }
        ),
    )
    result = evaluate(response, codes, table)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "filter-law-decision-0.1",
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
                "types": result["types"],
                "low_pass_edges_hz": result["low_pass_edges_hz"],
                "high_pass_edges_hz": result["high_pass_edges_hz"],
            }
        )
    )


if __name__ == "__main__":
    main()
