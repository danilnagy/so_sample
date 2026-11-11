"""Check the FX pattern observation: reception, the control run, and a table per effect."""

import argparse
import hashlib
import json
import math
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.fx_descriptor_method import _prepare
from scripts.fx_pattern_method import SETTINGS, describe_steps
from scripts.prepare_fx_pattern_observation import (
    CHAIN,
    CONTROL_PATTERN,
    DIRECTORY,
    KEY_HZ,
    REGISTRATION,
)

DECISION = "fx-pattern-decision-001.json"


def nearest_key(hz):
    """The key 1..16 whose pitch is nearest, and the distance in cents."""
    best = min(range(16), key=lambda k: abs(math.log2(hz / KEY_HZ[k])))
    return best + 1, 1200 * math.log2(hz / KEY_HZ[best])


def control_run(steps):
    for k, step in enumerate(steps):
        w = step["windows"][0]
        if w is None or step["onsets"] != 1:
            return False
        if abs(1200 * math.log2(w["hz"] / KEY_HZ[k])) > 20:
            return False
    return True


def table(described):
    out = {}
    for pattern, steps in zip(CHAIN, described, strict=True):
        rows = []
        for k, step in enumerate(steps):
            row = {"step": k + 1, "expected_key": k + 1, "onsets": step["onsets"], "windows": []}
            for w in step["windows"]:
                if w is None:
                    row["windows"].append(None)
                    continue
                key, cents = nearest_key(w["hz"])
                row["windows"].append(
                    {
                        "level_db": w["level_db"],
                        "hz": w["hz"],
                        "key": key if w["level_db"] > -30 else None,
                        "cents_from_key": cents,
                    }
                )
            rows.append(row)
        out[pattern] = rows
    return out


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
    measure_path = folder / "fx-pattern-measurements-001.json"
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
        "analysis_version": "fx-pattern-native-check-0.1",
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
    rows = table(described)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "fx-pattern-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "patterns": {str(p): rows[p] for p in CHAIN},
            }
        ),
    )
    decision = {
        "analysis_version": "fx-pattern-decision-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": sha256_file(native_path),
        "measurements_sha256": sha256_file(measure_path),
        "hypotheses": {
            "exact_reception": checks["entire_actual_body_and_packets_match_target"],
            "control_run": control_run(described[CHAIN.index(CONTROL_PATTERN)]),
        },
        "effects": {
            str(p): [
                {
                    "step": r["step"],
                    "onsets": r["onsets"],
                    "keys": [None if w is None else w["key"] for w in r["windows"]],
                    "levels_db": [
                        None if w is None else round(w["level_db"]) for w in r["windows"]
                    ],
                }
                for r in rows[p]
            ]
            for p in CHAIN
        },
        "limits": registration["limits"],
    }
    write_bytes(decision_path, json_bytes(decision))
    print(json.dumps({"hypotheses": decision["hypotheses"]}))
    for p in CHAIN:
        label = "control" if p == CONTROL_PATTERN else f"FX {p:>2}"
        keys = [r["keys"][0] for r in rows[p]]
        onsets = [r["onsets"] for r in rows[p]]
        print(f"{label}: keys@100ms {keys} onsets {onsets}")


if __name__ == "__main__":
    main()
