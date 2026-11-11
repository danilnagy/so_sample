"""Verify fixed generated pitch13 or14 reception separately from frequency evidence."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.prepare_generated_sound3_pitch_pair import DIRECTORIES, REGISTRATION, pair_preservation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leg", choices=("reference", "candidate"), required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    index = ("reference", "candidate").index(args.leg)
    directory = root / "experiments" / DIRECTORIES[index]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    leg = registration["expected_capture_sequence"][index]
    source_path = root / registration["source_artifact"]
    target_path = directory / "edited.symbols.npz"
    capture_path = directory / "capture.wav"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    output = directory / "hardware-recapture-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, target_path, capture_path, artifact_path], False
    )
    recorded = load_artifact(artifact_path)
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
        or sha256_file(target_path) != leg["edited_artifact_sha256"]
        or sha256_file(directory / "restore.wav") != leg["restore_wav_sha256"]
        or sha256_file(directory / "software-validation.json") != leg["software_validation_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture_path)
    ):
        raise ValueError("Registered source,target or independent recapture identity differs")
    source, target, actual = [
        decode_artifact(item)
        for item in (load_artifact(source_path), load_artifact(target_path), recorded)
    ]
    checks = dict(
        pair_preservation(source, actual, leg["raw_pitch_value"]),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == leg["expected_body_sha256"],
        entire_actual_body_matches_target=actual.encoded_body == target.encoded_body,
        entire_actual_packets_match_target=actual.packets == target.packets,
    )
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "fixed-pitch-pair-native-recapture-check-0.1",
                "hardware_verified": False,
                "passed": all(checks.values()),
                "checks": checks,
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": sha256_file(capture_path),
                "artifact_sha256": sha256_file(artifact_path),
                "artifact_path": artifact_path.relative_to(root).as_posix(),
                "native_frame": frame_report(actual),
                "audible_frequency_evaluated": False,
                "pitch_field_writer_enabled": False,
                "limits": registration["limits"],
            }
        ),
    )
    if not all(checks.values()):
        raise ValueError("Pitch recapture differs from fixed complete target; report retained")


if __name__ == "__main__":
    main()
