"""Check the FX rules test: exact reception, control run, and which rule each effect obeys."""

import argparse
import hashlib
import json
import math
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.fx_descriptor_method import _prepare
from scripts.fx_pattern_method import describe_steps
from scripts.prepare_fx_rules_test import (
    CHAIN,
    CONTROL_PATTERN,
    DIRECTORY,
    FX13_RULES,
    FX14_RULES,
    HOLDS,
    KEY_HZ,
    REGISTRATION,
    SETTINGS,
    predictions,
)

DECISION = "fx-rules-decision-001.json"
LATE_WINDOW = 1  # index of the 100 ms window in SETTINGS["window_starts_ms"]


def nearest_key(hz):
    best = min(range(16), key=lambda k: abs(math.log2(hz / KEY_HZ[k])))
    return best + 1


def heard_keys(steps, window=LATE_WINDOW):
    keys = []
    for step in steps:
        w = step["windows"][window]
        keys.append(None if w is None or w["level_db"] < -30 else nearest_key(w["hz"]))
    return keys


def control_run(steps):
    for k, step in enumerate(steps):
        w = step["windows"][LATE_WINDOW]
        if w is None or step["onsets"] != 1:
            return False
        if abs(1200 * math.log2(w["hz"] / KEY_HZ[k])) > 20:
            return False
    return True


def evaluate(described):
    heard = {pattern: heard_keys(steps) for pattern, steps in zip(CHAIN, described, strict=True)}
    table = predictions()
    support = {}
    for fx, rules in ((14, FX14_RULES), (13, FX13_RULES)):
        patterns = [p for p, (f, _, _) in HOLDS.items() if f == fx]
        support[str(fx)] = {
            rule: all(
                heard[p][step - 1] == key for p in patterns for step, key in table[p][rule].items()
            )
            for rule in rules
        }
    classification = {
        fx: (holding[0] if len(holding) == 1 else "no_single_rule")
        for fx, rules in support.items()
        for holding in [[r for r, ok in rules.items() if ok]]
    }
    return {
        "heard_keys_at_100ms": {str(p): keys for p, keys in heard.items()},
        "heard_keys_at_30ms": {
            str(p): heard_keys(steps, 0) for p, steps in zip(CHAIN, described, strict=True)
        },
        "onsets": {
            str(p): [s["onsets"] for s in steps] for p, steps in zip(CHAIN, described, strict=True)
        },
        "rule_support": support,
        "classification": classification,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    pins = {
        "scripts/fx_pattern_method.py": registration["method_script_sha256"],
        "scripts/fx_descriptor_method.py": registration["descriptor_method_script_sha256"],
    }
    if any(sha256_file(root / path) != pin for path, pin in pins.items()):
        raise ValueError("A frozen method changed since registration")
    if registration["method_settings"] != SETTINGS or registration["holds"] != {
        str(k): list(v) for k, v in HOLDS.items()
    }:
        raise ValueError("Frozen settings or plan changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "fx-rules-measurements-001.json"
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
        "analysis_version": "fx-rules-native-check-0.1",
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
    _, _, _, first = _prepare(playback, SETTINGS)
    starts = [first + i * 16 * SETTINGS["step_seconds"] for i in range(len(CHAIN))]
    described = describe_steps(playback, starts, (CHAIN.index(CONTROL_PATTERN), 1), SETTINGS)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "fx-rules-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "described": {str(p): d for p, d in zip(CHAIN, described, strict=True)},
            }
        ),
    )
    result = evaluate(described)
    decision = {
        "analysis_version": "fx-rules-decision-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": sha256_file(native_path),
        "measurements_sha256": sha256_file(measure_path),
        "hypotheses": {
            "exact_reception": checks["entire_actual_body_and_packets_match_target"],
            "control_run": control_run(described[CHAIN.index(CONTROL_PATTERN)]),
        },
        **result,
        "limits": registration["limits"],
    }
    write_bytes(decision_path, json_bytes(decision))
    print(
        json.dumps(
            {
                "hypotheses": decision["hypotheses"],
                "classification": result["classification"],
                "rule_support": result["rule_support"],
            }
        )
    )
    for p in CHAIN:
        label = (
            "control"
            if p == CONTROL_PATTERN
            else f"P{p} FX{HOLDS[p][0]} hold {HOLDS[p][1]}-{HOLDS[p][2]}"
        )
        print(
            f"{label:>22}: keys@100 {result['heard_keys_at_100ms'][str(p)]} onsets {result['onsets'][str(p)]}"
        )


if __name__ == "__main__":
    main()
