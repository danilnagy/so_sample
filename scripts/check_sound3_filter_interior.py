"""Retain both interior scalar-order alternatives and require a complete center return."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_probe import recorded_report
from scripts.check_sound3_filter_range import alternative_values, mask_preserved
from scripts.prepare_sound3_filter_interior import CAPTURE_IDS, REGISTRATION


def interior_report(base, lowpass, highpass, returned, registration):
    frames = [lowpass, highpass, returned]
    reports = [recorded_report(base, frame, registration) for frame in frames]
    scopes = [
        all(report["preservation_checks"].values()) and mask_preserved(base, frame)
        for report, frame in zip(reports, frames)
    ]
    contiguous = [
        report["raw_Sound3_fields"]["after"]["uninterpreted_candidate_values"] for report in reports
    ]
    alternative = [alternative_values(frame) for frame in frames]
    branches = {}
    for name, values in (("contiguous", contiguous), ("alternative", alternative)):
        bounds = registration["branch_scalar_order_hypotheses"][name]
        branches[name] = {
            side + "_all_values_within_registered_strict_bounds": scopes[index]
            and all(
                bounds[side + "_strict_bounds"][0] < value < bounds[side + "_strict_bounds"][1]
                for value in values[index]
            )
            for index, side in enumerate(("lowpass", "highpass"))
        }
        branches[name]["both_branch_order_hypotheses_supported"] = all(branches[name].values())
    target = registration["expected_capture_sequence"][2]
    return_checks = {
        "entire_body_matches_registered_center_sha256": hashlib.sha256(
            returned.encoded_body
        ).hexdigest()
        == target["expected_complete_body_sha256"],
        "entire_body_and_every_packet_equal_independent_center": returned.encoded_body
        == base.encoded_body
        and returned.packets == base.packets,
        "all_contiguous_values_match_registered_center": contiguous[2]
        == target["expected_contiguous_values"],
        "all_alternative_values_match_registered_center": alternative[2]
        == target["expected_alternative_values"],
    }
    return {
        "source_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "all_actual_native_controls_pass": all(
            all(report["native_checks"].values()) for report in reports
        ),
        "strict_candidate_mask_and_all_other_state_preserved_by_leg": scopes,
        "pitch14_and_volume36_preserved": all(
            report["raw_Sound3_fields"]["after"]["first_low5_values"]
            == registration["expected_pitch_values"]
            and report["raw_Sound3_fields"]["after"]["volume_values"]
            == registration["expected_volume_values"]
            for report in reports
        ),
        "contiguous_values_by_leg": contiguous,
        "alternative_values_by_leg": alternative,
        "candidate_changed_from_center_by_leg": [
            bool(report["candidate_changed_steps"]) for report in reports
        ],
        "values_uniform_by_leg": [len(set(values)) == 1 for values in contiguous],
        "branch_scalar_order_checks": branches,
        "exact_return_checks": return_checks,
        "all_exact_center_return_checks_pass": all(return_checks.values()),
        "location_reports_against_independent_center": reports,
        "interior_values_guessed": False,
        "filter_bit_order_width_mode_or_Hz_scale_confirmed": False,
        "filter_writer_enabled": False,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["source_artifact"]
    source_folder = root / "experiments/event-058-e-sound3-filter-A-center"
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    captures = [directory / "capture.wav" for directory in directories]
    paths = [directory / "derived/analysis-001/capture.symbols.npz" for directory in directories]
    output = root / "experiments/sound3-filter-A-interior-results-001.json"
    validate_outputs([output], [registration_path, source_path, *paths, *captures], False)
    recorded = [load_artifact(path) for path in paths]
    pins = (
        (source_path, registration["source_artifact_sha256"]),
        (root / registration["source_capture"], registration["source_capture_sha256"]),
        (
            source_folder / "hardware-observation-001.json",
            registration["source_observation_sha256"],
        ),
        (
            source_folder / "center-native-results-001.json",
            registration["source_native_results_sha256"],
        ),
        (
            source_folder / "center-audio-comparison-results-001.json",
            registration["source_audio_comparison_sha256"],
        ),
    )
    if any(sha256_file(path) != digest for path, digest in pins) or any(
        item.metadata["source_sha256"] != sha256_file(capture)
        for item, capture in zip(recorded, captures)
    ):
        raise ValueError("Registered center evidence or independent capture identity differs")
    base = decode_artifact(load_artifact(source_path))
    frames = [decode_artifact(item) for item in recorded]
    report = interior_report(base, *frames, registration)
    report.update(
        analysis_version="recorded-FILTER-interior-branches-and-complete-center-return-check-0.1",
        hardware_verified=False,
        registration_sha256=sha256_file(registration_path),
        captures=[
            {
                "experiment_id": directory.name,
                "capture_sha256": sha256_file(capture),
                "artifact_sha256": sha256_file(path),
                "artifact_path": path.relative_to(root).as_posix(),
                "native_frame": frame_report(frame),
            }
            for directory, capture, path, frame in zip(directories, captures, paths, frames)
        ],
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if (
        not report["source_body_matches_registration"]
        or not report["all_actual_native_controls_pass"]
    ):
        raise ValueError("FILTER interior native control failed; report retained")


if __name__ == "__main__":
    main()
