"""Check the footer position map: exact reception, then the frozen per-note decision."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_fx_multi_step_pitch_method import SETTINGS, decide, note_tracks, step_results
from scripts.prepare_pattern1_fx_position_map import (
    DIRECTORY,
    PREDICTIONS,
    REGISTRATION,
    position_map_checks,
)

DECISION = "pattern1-FX-position-map-decision-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    for name, key in (
        ("scripts/pattern1_fx_multi_step_pitch_method.py", "method_script_sha256"),
        ("scripts/pattern1_fx_step_pitch_method.py", "step1_method_script_sha256"),
    ):
        if sha256_file(root / name) != registration[key]:
            raise ValueError(f"{name} changed since registration")
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
        position_map_checks(base, actual),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        entire_actual_body_and_packets_match_target=actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        capture_is_new=capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    )
    native = {
        "analysis_version": "FX-position-map-native-check-0.1",
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
        raise ValueError("Native reception failed; report retained")
    tracks = note_tracks(playback)
    results = step_results(tracks, registration["reference_frequency_hz"])
    write_bytes(
        pitch_path,
        json_bytes(
            {
                "analysis_version": "FX-position-map-note-pitch-tracks-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "tracks": tracks,
                "steps": {str(k): v for k, v in results.items()},
            }
        ),
    )
    decision = decide(results, PREDICTIONS)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "FX-position-map-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "pitch_results_sha256": sha256_file(pitch_path),
                "steps": {
                    str(k): {"median": v["median"]["class"], "per_loop": v["per_loop"]}
                    for k, v in results.items()
                },
                **decision,
                "limits": registration["limits"],
            }
        ),
    )
    print(
        json.dumps(
            {
                "native": native["passed"],
                "steps": {k: v["median"]["class"] for k, v in results.items()},
                "classification": decision["classification"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
