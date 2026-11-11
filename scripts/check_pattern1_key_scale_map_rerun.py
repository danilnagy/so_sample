"""Check the keyboard scale map rerun: exact reception, then the grid-only decision."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_key_scale_grid_method import SETTINGS, decide, intervals, step_frequencies
from scripts.prepare_pattern1_key_scale_map import scale_checks
from scripts.prepare_pattern1_key_scale_map_rerun import DIRECTORY, MODELS, REGISTRATION

DECISION = "pattern1-key-scale-map-rerun-decision-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / "scripts/pattern1_key_scale_grid_method.py")
        != registration["method_script_sha256"]
    ):
        raise ValueError("Frozen method changed since registration")
    if registration["method_settings"] != SETTINGS or registration["models_cents"] != MODELS:
        raise ValueError("Frozen settings or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    source_path = root / registration["source_artifact"]
    native_path = folder / "hardware-recapture-results-001.json"
    pitch_path = folder / "key-frequency-results-001.json"
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
        scale_checks(base, actual),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        entire_actual_body_and_packets_match_target=actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        capture_is_new=capture_hash
        not in {
            registration["source_capture_sha256"],
            registration["first_capture_sha256"],
            registration["restore_wav_sha256"],
        },
    )
    native = {
        "analysis_version": "key-scale-map-rerun-native-check-0.1",
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
    info, steps = step_frequencies(playback, SETTINGS)
    table = intervals(steps)
    write_bytes(
        pitch_path,
        json_bytes(
            {
                "analysis_version": "key-scale-map-rerun-frequencies-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                **info,
                "step_frequencies_hz": {str(k): v for k, v in steps.items()},
                "intervals": None
                if table is None
                else {
                    "step1_hz": table["step1_hz"],
                    "steps": {str(k): v for k, v in table["steps"].items()},
                },
            }
        ),
    )
    decision = decide(table, MODELS)
    cents = (
        None if table is None else {str(k): v["median_cents"] for k, v in table["steps"].items()}
    )
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "key-scale-map-rerun-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "frequency_results_sha256": sha256_file(pitch_path),
                "step1_hz": None if table is None else table["step1_hz"],
                "measured_cents": cents,
                **decision,
                "limits": registration["limits"],
            }
        ),
    )
    print(
        json.dumps(
            {
                "native": native["passed"],
                "step1_hz": None if table is None else round(table["step1_hz"], 2),
                "cents": None
                if cents is None
                else {k: None if v is None else round(v, 1) for k, v in cents.items()},
                "classification": decision["classification"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
