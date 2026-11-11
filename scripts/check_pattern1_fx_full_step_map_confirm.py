"""Check the full step map confirmation: exact backup, then the per-note-gate decision."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_fx_multi_step_pitch_method import decide, step_results
from scripts.pattern1_fx_note_gate_method import SETTINGS, note_tracks
from scripts.prepare_pattern1_fx_full_step_map import PREDICTIONS, full_map_checks
from scripts.prepare_pattern1_fx_full_step_map_confirm import (
    DIRECTORY,
    METHOD_FILES,
    REGISTRATION,
)

DECISION = "pattern1-FX-full-step-map-confirm-decision-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    for key, path in METHOD_FILES.items():
        if sha256_file(root / path) != registration[key]:
            raise ValueError(f"{path} changed since registration")
    if registration["method_settings"] != SETTINGS or registration["predictions"] != PREDICTIONS:
        raise ValueError("Frozen settings or predictions changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    source_path = root / registration["source_artifact"]
    native_path = folder / "hardware-recapture-results-001.json"
    pitch_path = folder / "pitch-track-results-001.json"
    decision_path = root / "experiments" / DECISION
    validate_outputs(
        [native_path, pitch_path, decision_path],
        [capture, playback, artifact_path, target_path, source_path],
        False,
    )
    if sha256_file(target_path) != registration["edited_artifact_sha256"]:
        raise ValueError("Registered target changed")
    artifact = load_artifact(artifact_path)
    capture_hash = sha256_file(capture)
    if artifact.metadata["source_sha256"] != capture_hash:
        raise ValueError("Analysis artifact is not from capture.wav")
    base = decode_artifact(load_artifact(source_path))
    target = decode_artifact(load_artifact(target_path))
    actual = decode_artifact(artifact)
    checks = dict(
        full_map_checks(base, actual),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        entire_actual_body_and_packets_match_target=actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        capture_is_new=capture_hash
        not in {registration["source_capture_sha256"], registration["first_capture_sha256"]},
    )
    native = {
        "analysis_version": "FX-full-step-map-confirm-native-check-0.1",
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
        raise ValueError("The new backup does not match the target; report retained")
    tracks = note_tracks(playback, SETTINGS)
    results = step_results(tracks, registration["reference_frequency_hz"], SETTINGS)
    write_bytes(
        pitch_path,
        json_bytes(
            {
                "analysis_version": "FX-full-step-map-confirm-note-pitch-tracks-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "tracks": tracks,
                "steps": {str(k): v for k, v in results.items()},
            }
        ),
    )
    decision = decide(results, PREDICTIONS, SETTINGS)
    observed = {str(k): v["median"]["class"] for k, v in results.items()}
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "FX-full-step-map-confirm-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "pitch_results_sha256": sha256_file(pitch_path),
                "steps": {
                    str(k): {
                        "median": v["median"]["class"],
                        "max_ratio": v["median"].get("max_ratio"),
                        "per_loop": v["per_loop"],
                    }
                    for k, v in results.items()
                },
                "observed_effect_steps": [int(s) for s, c in observed.items() if c == "effect"],
                **decision,
                "limits": registration["limits"],
            }
        ),
    )
    print(
        json.dumps(
            {
                "native": native["passed"],
                "observed_effect_steps": [int(s) for s, c in observed.items() if c == "effect"],
                "other_classes": {s: c for s, c in observed.items() if c not in ("effect", "none")},
                "classification": decision["classification"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
