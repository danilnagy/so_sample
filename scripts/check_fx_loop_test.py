"""Check the loop length test: exact reception, control run, and a loop length per effect."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_fx_pattern_observation import control_run, nearest_key
from scripts.fx_descriptor_method import _prepare
from scripts.fx_pattern_method import SETTINGS, describe_steps
from scripts.prepare_fx_loop_test import (
    CHAIN,
    CONTROL_PATTERN,
    DIRECTORY,
    HELD,
    HOLD_STEPS,
    LOOP_LENGTHS,
    REGISTRATION,
    loop_prediction,
)

DECISION = "fx-loop-decision-001.json"


def heard_keys(steps):
    keys = []
    for step in steps:
        w = step["windows"][0]
        keys.append(None if w is None or w["level_db"] < -30 else nearest_key(w["hz"])[0])
    return keys


def classify(keys):
    matches = [
        n for n in LOOP_LENGTHS if all(keys[s - 1] == loop_prediction(n)[s - 1] for s in HOLD_STEPS)
    ]
    return f"loop_{matches[0]}" if len(matches) == 1 else "unresolved"


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
    if registration["method_settings"] != SETTINGS:
        raise ValueError("Frozen settings changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "fx-loop-measurements-001.json"
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
        "analysis_version": "fx-loop-native-check-0.1",
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
    keys = {pattern: heard_keys(steps) for pattern, steps in zip(CHAIN, described, strict=True)}
    onsets = {
        pattern: [s["onsets"] for s in steps]
        for pattern, steps in zip(CHAIN, described, strict=True)
    }
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "fx-loop-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "described": {str(p): d for p, d in zip(CHAIN, described, strict=True)},
            }
        ),
    )
    result = {
        str(fx): {
            "pattern": pattern,
            "keys_at_100ms": keys[pattern],
            "onsets": onsets[pattern],
            "classification": classify(keys[pattern]),
        }
        for pattern, fx in HELD.items()
    }
    decision = {
        "analysis_version": "fx-loop-decision-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": sha256_file(native_path),
        "measurements_sha256": sha256_file(measure_path),
        "hypotheses": {
            "exact_reception": checks["entire_actual_body_and_packets_match_target"],
            "control_run": control_run(described[CHAIN.index(CONTROL_PATTERN)]),
        },
        "effects": result,
        "control_keys": keys[CONTROL_PATTERN],
        "limits": registration["limits"],
    }
    write_bytes(decision_path, json_bytes(decision))
    print(json.dumps({"hypotheses": decision["hypotheses"]}))
    for fx, v in result.items():
        print(
            f"FX {fx:>2}: {v['classification']:>10} keys {v['keys_at_100ms']} onsets {v['onsets']}"
        )


if __name__ == "__main__":
    main()
