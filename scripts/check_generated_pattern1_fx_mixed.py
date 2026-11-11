"""Check exact mixed-effect reception without inferring its playback sequence from bytes."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.prepare_generated_pattern1_fx_mixed import DIRECTORY, REGISTRATION, mixed_checks


def reception_checks(base, target, actual, registration):
    return dict(
        mixed_checks(base, actual),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        entire_actual_body_and_packets_match_target=actual.encoded_body == target.encoded_body
        and actual.packets == target.packets,
    )


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    folder = root / "experiments" / DIRECTORY
    source_path = root / registration["source_artifact"]
    target_path = folder / "edited.symbols.npz"
    capture_path = folder / "capture.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    output = folder / "hardware-recapture-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, target_path, capture_path, artifact_path], False
    )
    pins = [
        (source_path, registration["source_artifact_sha256"]),
        (root / registration["source_capture"], registration["source_capture_sha256"]),
        (root / registration["source_observation"], registration["source_observation_sha256"]),
        (target_path, registration["edited_artifact_sha256"]),
        (folder / "restore.wav", registration["restore_wav_sha256"]),
        (folder / "software-validation.json", registration["software_validation_sha256"]),
    ]
    recorded = load_artifact(artifact_path)
    capture_hash = sha256_file(capture_path)
    if (
        any(sha256_file(path) != digest for path, digest in pins)
        or recorded.metadata["source_sha256"] != capture_hash
        or capture_hash
        in {registration["source_capture_sha256"], registration["restore_wav_sha256"]}
    ):
        raise ValueError(
            "Frozen mixed source/target or independent physical capture identity differs"
        )
    base, target, actual = [
        decode_artifact(item)
        for item in (load_artifact(source_path), load_artifact(target_path), recorded)
    ]
    checks = reception_checks(base, target, actual, registration)
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "mixed-footer-global7-native-recapture-check-0.1",
                "hardware_verified": False,
                "passed": all(checks.values()),
                "checks": checks,
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": capture_hash,
                "artifact_sha256": sha256_file(artifact_path),
                "artifact_path": artifact_path.relative_to(root).as_posix(),
                "native_frame": frame_report(actual),
                "audible_effect_sequence_evaluated": False,
                "per_step_nibble_order_confirmed": False,
                "mixed_FX_writer_enabled": False,
                "limits": registration["limits"],
            }
        ),
    )
    if not all(checks.values()):
        raise ValueError("Mixed target reception differs; failed report retained")


if __name__ == "__main__":
    main()
