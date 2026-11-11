"""Check a generated timing pair leg against its exact registered native target."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.prepare_swing_timing_pair import DIRECTORIES, target_checks


def recapture_checks(base, target, actual, leg):
    return dict(
        target_checks(base, actual, leg["swing_byte"]),
        supplied_target_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == leg["expected_body_sha256"],
        entire_recapture_body_matches_target=actual.encoded_body == target.encoded_body,
        entire_recapture_packets_match_target=actual.packets == target.packets,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--swing", type=int, choices=(0, 6), required=True)
    parser.add_argument("--artifact", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    index = (0, 6).index(args.swing)
    directory = root / "experiments" / DIRECTORIES[index]
    registration_path = root / "experiments/swing-timing-pair-registration-001.json"
    registration = json.loads(registration_path.read_text())
    leg = registration["expected_capture_sequence"][index]
    source_path = root / registration["source_artifact"]
    target_path = directory / "edited.symbols.npz"
    artifact_path = args.artifact or directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    output = directory / "hardware-recapture-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, target_path, capture, artifact_path], False
    )
    recorded = load_artifact(artifact_path)
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(target_path) != leg["edited_artifact_sha256"]
        or sha256_file(directory / "restore.wav") != leg["restore_wav_sha256"]
        or sha256_file(directory / "software-validation.json") != leg["software_validation_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Registered timing source, target or recapture identity differs")
    base, target, actual = [
        decode_artifact(item)
        for item in (load_artifact(source_path), load_artifact(target_path), recorded)
    ]
    checks = recapture_checks(base, target, actual, leg)
    report = {
        "analysis_version": "swing-timing-recapture-check-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "checks": checks,
        "passed": all(checks.values()),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "artifact_path": artifact_path.relative_to(root).as_posix(),
        "native_frame": frame_report(actual),
        "timing_effect_evaluated": False,
        "limits": [
            "This checks stored data only; ordinary playback timing and manual hardware observations remain separate"
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Timing recapture differs; report retained")


if __name__ == "__main__":
    main()
