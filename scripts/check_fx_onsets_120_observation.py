"""Check the FX onsets observation at 120 BPM: reception, control run, per-step onsets."""

import argparse
import hashlib
import json
import math
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_fx_pattern_observation import nearest_key
from scripts.fx_descriptor_method import _prepare
from scripts.fx_pattern_method import describe_steps
from scripts.prepare_fx_onsets_120_observation import (
    CHAIN,
    CONTROL_PATTERN,
    CYCLES,
    DIRECTORY,
    HELD,
    KEY_HZ,
    REGISTRATION,
    SETTINGS,
)

DECISION = "fx-onsets-120-decision-001.json"


def control_run(steps):
    for k, step in enumerate(steps):
        w = step["windows"][0]
        if w is None or step["onsets"] != 1:
            return False
        if abs(1200 * math.log2(w["hz"] / KEY_HZ[k])) > 20:
            return False
    return True


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
    measure_path = folder / "fx-onsets-120-measurements-001.json"
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
        "analysis_version": "fx-onsets-120-native-check-0.1",
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
    cycle = len(CHAIN) * 16 * SETTINGS["step_seconds"]
    starts, labels = [], []
    for c in range(CYCLES):
        for i, pattern in enumerate(CHAIN):
            starts.append(first + c * cycle + i * 16 * SETTINGS["step_seconds"])
            labels.append((c, pattern))
    described = describe_steps(playback, starts, (labels.index((0, CONTROL_PATTERN)), 1), SETTINGS)
    per_pattern = {}
    for (c, pattern), steps in zip(labels, described, strict=True):
        per_pattern.setdefault(pattern, []).append(
            [
                {
                    "step": k + 1,
                    "onsets": s["onsets"],
                    "key": None
                    if s["windows"][0] is None or s["windows"][0]["level_db"] < -30
                    else nearest_key(s["windows"][0]["hz"])[0],
                    "level_db": None
                    if s["windows"][0] is None
                    else round(s["windows"][0]["level_db"]),
                }
                for k, s in enumerate(steps)
            ]
        )
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "fx-onsets-120-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "patterns": {str(p): v for p, v in per_pattern.items()},
            }
        ),
    )
    control_ok = all(
        control_run(steps)
        for (c, pattern), steps in zip(labels, described, strict=True)
        if pattern == CONTROL_PATTERN
    )
    decision = {
        "analysis_version": "fx-onsets-120-decision-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": sha256_file(native_path),
        "measurements_sha256": sha256_file(measure_path),
        "hypotheses": {
            "exact_reception": checks["entire_actual_body_and_packets_match_target"],
            "control_run": control_ok,
        },
        "effects": {str(fx): {"pattern": p, "cycles": per_pattern[p]} for p, fx in HELD.items()},
        "limits": registration["limits"],
    }
    write_bytes(decision_path, json_bytes(decision))
    print(json.dumps({"hypotheses": decision["hypotheses"]}))
    for p, fx in HELD.items():
        first_cycle = per_pattern[p][0]
        print(
            f"FX {fx:>2}: onsets {[r['onsets'] for r in first_cycle]} keys@50ms {[r['key'] for r in first_cycle]} levels {[r['level_db'] for r in first_cycle]}"
        )


if __name__ == "__main__":
    main()
