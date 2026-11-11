"""Check the swing law test: exact reception, then the even-step position at swing 18."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.globals import swing
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.prepare_swing_law_test import (
    DIRECTORY,
    MAX_SPREAD,
    MODELS,
    REGISTRATION,
    SWING,
    TOLERANCE,
)
from scripts.swing_onset_method import SETTINGS, onsets, summarize

DECISION = "swing-law-decision-001.json"


def decide(summary):
    position, spread = summary["median_position"], summary["position_spread"]
    support = {
        name: position is not None
        and abs(position - value) <= TOLERANCE
        and spread is not None
        and spread < MAX_SPREAD
        for name, value in MODELS.items()
    }
    holding = [m for m, ok in support.items() if ok]
    return {
        "median_position": position,
        "delay_in_steps": None if position is None else 2 * (position - 0.5),
        "model_support": support,
        "classification": holding[0] if len(holding) == 1 else "other_or_inconclusive",
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / "scripts/swing_onset_method.py") != registration["method_script_sha256"]
        or registration["method_settings"] != SETTINGS
        or registration["models_position"] != MODELS
    ):
        raise ValueError("Frozen method or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "swing-measurements-001.json"
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
        "swing_byte": swing(actual) == SWING,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "swing-law-native-check-0.1",
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
    times = onsets(playback, SETTINGS)
    summary = summarize(times, SETTINGS)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "swing-law-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "onset_seconds": times,
                **summary,
            }
        ),
    )
    decision = decide(summary)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "swing-law-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "measurements_sha256": sha256_file(measure_path),
                "swing": SWING,
                **decision,
                "position_spread": summary["position_spread"],
                "median_step_seconds": summary["median_step_seconds"],
                "limits": registration["limits"],
            }
        ),
    )
    print(
        json.dumps(
            {
                "native": True,
                "onsets": summary["onset_count"],
                "loops": summary["loops_measured"],
                "median_position": None
                if decision["median_position"] is None
                else round(decision["median_position"], 4),
                "spread": None
                if summary["position_spread"] is None
                else round(summary["position_spread"], 4),
                "step_seconds": None
                if summary["median_step_seconds"] is None
                else round(summary["median_step_seconds"], 4),
                "classification": decision["classification"],
            }
        )
    )


if __name__ == "__main__":
    main()
