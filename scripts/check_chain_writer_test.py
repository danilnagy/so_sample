"""Check the chain writer test: exact reception, then which pattern each loop played."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.globals import pattern_chain
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_pattern_chain_observation import loop_matches
from scripts.pattern1_key_scale_grid_method import step_frequencies
from scripts.prepare_chain_writer_test import CHAIN, DIRECTORY, MODELS, REGISTRATION, SETTINGS

DECISION = "chain-writer-decision-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / "scripts/pattern1_key_scale_grid_method.py")
        != registration["method_script_sha256"]
        or registration["method_settings"] != SETTINGS
        or registration["models_hz_by_loop"] != MODELS
    ):
        raise ValueError("Frozen method or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    pitch_path = folder / "loop-frequency-results-001.json"
    decision_path = root / "experiments" / DECISION
    validate_outputs(
        [native_path, pitch_path, decision_path],
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
        "planned_chain": pattern_chain(actual) == CHAIN,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "chain-writer-native-check-0.1",
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
    info, steps = step_frequencies(playback, SETTINGS)
    write_bytes(
        pitch_path,
        json_bytes(
            {
                "analysis_version": "chain-writer-frequencies-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                **info,
                "step_frequencies_hz": {str(k): v for k, v in steps.items()},
            }
        ),
    )
    matches = {
        name: loop_matches(steps, expected, SETTINGS["cents_tolerance"])
        for name, expected in MODELS.items()
    }
    support = {name: sum(m) >= 4 for name, m in matches.items()}
    supported = [name for name, ok in support.items() if ok]
    decision = {
        "analysis_version": "chain-writer-decision-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": sha256_file(native_path),
        "frequency_results_sha256": sha256_file(pitch_path),
        "loop_matches": matches,
        "model_support": support,
        "classification": supported[0] if len(supported) == 1 else "other_or_inconclusive",
        "limits": registration["limits"],
    }
    write_bytes(decision_path, json_bytes(decision))
    print(
        json.dumps(
            {
                "native": True,
                "loop_matches": matches,
                "classification": decision["classification"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
