"""Check the aux-nibble-002 test: exact reception, then the frozen measurement of the playback."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.audio import load_pcm_wav
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.aux_nibble2_method import SETTINGS, decide, measure
from scripts.prepare_aux_nibble_2_test import DIRECTORY, METHOD, PREDICTIONS, REGISTRATION

DECISION = "aux-nibble-decision-002.json"
MEASUREMENTS = "aux-nibble-measurements-002.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / METHOD) != registration["method_script_sha256"]
        or registration["method_settings"] != SETTINGS
        or {k: v for k, v in registration["predictions"].items() if k != "reception"} != PREDICTIONS
    ):
        raise ValueError("Frozen method or predictions changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / MEASUREMENTS
    decision_path = root / "experiments" / DECISION
    validate_outputs([native_path, measure_path, decision_path], [capture, playback, artifact_path, target_path], False)
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
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest() == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash != registration["restore_wav_sha256"],
    }
    native = {
        "analysis_version": "aux-nibble-2-native-check-0.1",
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
    samples, info = load_pcm_wav(playback)
    measured = measure(samples, info["sample_rate_hz"], registration["probes"])
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "aux-nibble-2-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                **measured,
            }
        ),
    )
    result = decide(measured, PREDICTIONS)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "aux-nibble-2-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "measurements_sha256": sha256_file(measure_path),
                "passes_measured": len(measured["passes"]),
                **result,
                "exploratory": {
                    "voice_onset_offsets_first_pass": {
                        str(v["held"]): v.get("onset_offsets_seconds") for v in measured["passes"][0]["voices"]
                    },
                    "fx_patterns_first_pass": measured["passes"][0]["fx"],
                },
            }
        ),
    )
    print(json.dumps({"native": True, "passes": len(measured["passes"]), **result}, indent=2))


if __name__ == "__main__":
    main()
