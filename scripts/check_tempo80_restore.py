"""Verify the first generated tempo restore against its target and genuine80 state."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo_control import comparison_checks


def restore_checks(base, target, actual, genuine, registration, observed_bpm=None):
    controls, fits, observed = comparison_checks(base, actual, registration, 120, observed_bpm)
    exact = {
        "supplied_target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "genuine80_body_matches_registration": hashlib.sha256(genuine.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_recapture_body_matches_supplied_target": actual.encoded_body == target.encoded_body,
        "entire_recapture_plain_packets_match_supplied_target": actual.packets == target.packets,
        "entire_recapture_body_matches_independent_genuine80": actual.encoded_body
        == genuine.encoded_body,
        "expected_geometry": len(actual.packets) == registration["expected_packet_count"]
        and actual.end_byte == registration["expected_frame_end_byte"],
        "displayed_BPM_independently_matches80": observed_bpm == 80
        if observed_bpm is not None
        else None,
    }
    return controls, fits, exact, observed


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-tempo80-001"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact", type=Path, default=directory / "derived/analysis-001/capture.symbols.npz"
    )
    parser.add_argument("--observed-bpm", type=int)
    args = parser.parse_args()
    registration_path = directory / "restore-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["baseline_artifact"]
    target_path = directory / "edited.symbols.npz"
    genuine_path = root / registration["genuine80_artifact"]
    capture = directory / "capture.wav"
    output = directory / "hardware-recapture-results-001.json"
    validate_outputs(
        [output],
        [registration_path, source_path, target_path, genuine_path, capture, args.artifact],
        False,
    )
    recorded = load_artifact(args.artifact)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(root / registration["baseline_capture"])
        != registration["baseline_capture_sha256"]
        or sha256_file(genuine_path) != registration["genuine80_artifact_sha256"]
        or sha256_file(target_path) != registration["edited_artifact_sha256"]
        or sha256_file(directory / "restore.wav") != registration["restore_wav_sha256"]
        or sha256_file(directory / "software-validation.json")
        != registration["software_validation_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Registered sources, generated restore or recapture identity differs")
    base, target, genuine, actual = [
        decode_artifact(artifact)
        for artifact in (
            load_artifact(source_path),
            load_artifact(target_path),
            load_artifact(genuine_path),
            recorded,
        )
    ]
    controls, fits, exact, observed = restore_checks(
        base, target, actual, genuine, registration, args.observed_bpm
    )
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "first-generated-tempo80-recapture-check-0.1",
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": sha256_file(capture),
                "artifact_sha256": sha256_file(args.artifact),
                "artifact_path": str(args.artifact),
                "control_checks": controls,
                "control_passed": all(controls.values()),
                "tempo_hypothesis_checks": fits,
                "exact_target_checks": exact,
                "observed_tempo": observed,
                "native_frame": frame_report(actual),
                "limits": registration["limits"],
            }
        ),
    )
    if not all(controls.values()):
        raise ValueError("Generated tempo restore control failed; report retained")


if __name__ == "__main__":
    main()
