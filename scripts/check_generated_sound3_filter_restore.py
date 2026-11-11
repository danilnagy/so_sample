"""Verify complete generated FILTER reception separately from user listening."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.prepare_generated_sound3_filter_pair import (
    DIRECTORIES,
    REGISTRATION,
    preservation_checks,
)


def reception_checks(source, target, actual, leg, registration):
    return dict(
        preservation_checks(source, actual, leg["raw_filter_value"], registration),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == leg["expected_body_sha256"],
        entire_actual_body_matches_target=actual.encoded_body == target.encoded_body,
        every_actual_packet_matches_target=actual.packets == target.packets,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leg", choices=("lowpass", "highpass"), required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    index = ("lowpass", "highpass").index(args.leg)
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if index == 1:
        prior_path = root / "experiments" / DIRECTORIES[0] / "hardware-observation-001.json"
        prior = json.loads(prior_path.read_text())
        if (
            not prior["hardware_verified"]
            or not all(prior["checks"].values())
            or prior["registration_sha256"] != sha256_file(registration_path)
        ):
            raise ValueError("Verified first generated FILTER reception and listening required")
    leg = registration["expected_capture_sequence"][index]
    folder = root / "experiments" / DIRECTORIES[index]
    source_path = root / registration["source_artifact"]
    target_path = folder / "edited.symbols.npz"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    capture_path = folder / "capture.wav"
    output = folder / "hardware-recapture-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, target_path, artifact_path, capture_path], False
    )
    recorded = load_artifact(artifact_path)
    pins = (
        (source_path, registration["source_artifact_sha256"]),
        (root / registration["source_capture"], registration["source_capture_sha256"]),
        (
            root
            / "experiments/event-061-h-return-sound3-filter-A-center/hardware-observation-001.json",
            registration["source_observation_sha256"],
        ),
        (target_path, leg["edited_artifact_sha256"]),
        (folder / "restore.wav", leg["restore_wav_sha256"]),
        (folder / "software-validation.json", leg["software_validation_sha256"]),
        (root / leg["independent_physical_artifact"], leg["independent_physical_artifact_sha256"]),
        (
            root / leg["independent_physical_observation"],
            leg["independent_physical_observation_sha256"],
        ),
    )
    if any(sha256_file(path) != digest for path, digest in pins) or recorded.metadata[
        "source_sha256"
    ] != sha256_file(capture_path):
        raise ValueError("Registered source, target or independent recapture identity differs")
    source, target, actual = [
        decode_artifact(item)
        for item in (load_artifact(source_path), load_artifact(target_path), recorded)
    ]
    checks = reception_checks(source, target, actual, leg, registration)
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "fixed-generated-FILTER-native-recapture-check-0.1",
                "hardware_verified": False,
                "passed": all(checks.values()),
                "checks": checks,
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": sha256_file(capture_path),
                "artifact_sha256": sha256_file(artifact_path),
                "artifact_path": artifact_path.relative_to(root).as_posix(),
                "native_frame": frame_report(actual),
                "audible_filter_evaluated": False,
                "filter_writer_enabled": False,
                "limits": registration["limits"],
            }
        ),
    )
    if not all(checks.values()):
        raise ValueError("Generated FILTER recapture differs from complete target; report retained")


if __name__ == "__main__":
    main()
