"""Check the kit-sharing test: exact reception of the restore with shared kit buffers."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.prepare_kit_sharing_test import DIRECTORY, REGISTRATION


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    folder = root / "experiments" / DIRECTORY
    capture = folder / "capture.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    validate_outputs([native_path], [capture, artifact_path, target_path], False)
    if sha256_file(target_path) != registration["edited_artifact_sha256"]:
        raise ValueError("Registered target changed")
    if sha256_file(folder / "packets.json") != registration["packets_json_sha256"]:
        raise ValueError("Registered packets changed")
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
        "capture_is_new": capture_hash != registration["restore_wav_sha256"],
    }
    write_bytes(
        native_path,
        json_bytes(
            {
                "analysis_version": "kit-sharing-native-check-0.1",
                "hardware_verified": False,
                "passed": all(checks.values()),
                "checks": checks,
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": capture_hash,
                "artifact_sha256": sha256_file(artifact_path),
                "native_frame": frame_report(actual),
            }
        ),
    )
    print(json.dumps({"passed": all(checks.values()), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise ValueError("Native reception failed; report retained")


if __name__ == "__main__":
    main()
