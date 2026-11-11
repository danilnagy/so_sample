"""Verify complete public-plan center63 reception independently of user listening."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_probe import recorded_report
from scripts.check_sound3_filter_range import mask_preserved


def center_reception_checks(source, target, actual, registration):
    report = recorded_report(source, actual, registration)
    fields = report["raw_Sound3_fields"]["after"]
    return dict(
        report["native_checks"],
        **report["preservation_checks"],
        source_body_matches_registration=hashlib.sha256(source.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        strict_candidate_mask_and_all_other_pattern1_state_preserved=mask_preserved(source, actual),
        all16_filter_fields_match_registered63=fields["uninterpreted_candidate_values"]
        == registration["expected_raw_filter_values"],
        pitch14_and_volume36_preserved=fields["first_low5_values"]
        == registration["expected_pitch_values"]
        and fields["volume_values"] == registration["expected_volume_values"],
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        entire_actual_body_and_every_packet_match_target=actual.encoded_body == target.encoded_body
        and actual.packets == target.packets,
    )


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments/sound3-generated-filter63-center-registration-001.json"
    registration = json.loads(registration_path.read_text())
    folder = root / "experiments" / registration["experiment_id"]
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
        (source_path, "source_artifact_sha256"),
        (root / registration["source_capture"], "source_capture_sha256"),
        (
            root / "experiments/edited-sound3-filter52-highpass-001/hardware-observation-001.json",
            "source_observation_sha256",
        ),
        (target_path, "edited_artifact_sha256"),
        (folder / "restore.wav", "restore_wav_sha256"),
        (folder / "plan.json", "plan_sha256"),
        (folder / "compile-report.json", "compile_report_sha256"),
        (root / registration["independent_center_artifact"], "independent_center_artifact_sha256"),
        (
            root
            / "experiments/event-061-h-return-sound3-filter-A-center/hardware-observation-001.json",
            "independent_center_observation_sha256",
        ),
    )
    if any(sha256_file(path) != registration[key] for path, key in pins) or recorded.metadata[
        "source_sha256"
    ] != sha256_file(capture_path):
        raise ValueError(
            "Registered FILTER source, target or independent recapture identity differs"
        )
    source, target, actual = [
        decode_artifact(item)
        for item in (load_artifact(source_path), load_artifact(target_path), recorded)
    ]
    checks = center_reception_checks(source, target, actual, registration)
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "public-observed-code-FILTER-center63-native-recapture-check-0.1",
                "hardware_verified": False,
                "passed": all(checks.values()),
                "checks": checks,
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": sha256_file(capture_path),
                "artifact_sha256": sha256_file(artifact_path),
                "artifact_path": artifact_path.relative_to(root).as_posix(),
                "native_frame": frame_report(actual),
                "audible_filter_evaluated": False,
                "broadband_bypass_or_general_filter_law_confirmed": False,
                "limits": registration["limits"],
            }
        ),
    )
    if not all(checks.values()):
        raise ValueError(
            "Public FILTER center recapture differs from complete target; report retained"
        )


if __name__ == "__main__":
    main()
