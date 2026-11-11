"""Require the complete independent B minimum return while retaining unknown maximum data."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_B_probe import B_probe_report
from scripts.prepare_sound3_filter_B_range import CAPTURE_IDS, REGISTRATION


def B_range_report(base, maximum, returned, registration):
    reports = [B_probe_report(base, frame, registration) for frame in (maximum, returned)]
    target = registration["expected_capture_sequence"][1]
    return_checks = {
        "entire_return_body_matches_registered_minimum": hashlib.sha256(
            returned.encoded_body
        ).hexdigest()
        == target["expected_complete_body_sha256"],
        "entire_return_body_and_every_packet_equal_independent_minimum": returned.encoded_body
        == base.encoded_body
        and returned.packets == base.packets,
        "all16_five_bit_return_values_match_registered_zero": reports[1][
            "raw_B_candidate_projections"
        ]["after"]["third_bits2_to6_values"]
        == target["expected_five_bit_values"],
        "all16_six_bit_return_values_match_registered_zero": reports[1][
            "raw_B_candidate_projections"
        ]["after"]["third_bits2_to7_values"]
        == target["expected_six_bit_values"],
    }
    return {
        "source_body_matches_registration": all(
            report["source_body_matches_registration"] for report in reports
        ),
        "both_actual_native_controls_pass": all(
            report["actual_native_controls_pass"] for report in reports
        ),
        "six_bit_mask_and_all_other_state_preserved_both_legs": all(
            report["B_candidate_mask_reports"]["third_primary_bits2_to7"][
                "only_candidate_bits_and_all_other_state_preserved"
            ]
            for report in reports
        ),
        "pitch14_volume36_and_filter_A63_preserved": all(
            report["pitch14_and_volume36_preserved"] and report["filter_A63_preserved"]
            for report in reports
        ),
        "maximum_candidate_changed": bool(
            reports[0]["B_candidate_mask_reports"]["third_primary_bits2_to7"]["changed_steps"]
        ),
        "five_bit_values_by_leg": [
            report["raw_B_candidate_projections"]["after"]["third_bits2_to6_values"]
            for report in reports
        ],
        "six_bit_values_by_leg": [
            report["raw_B_candidate_projections"]["after"]["third_bits2_to7_values"]
            for report in reports
        ],
        "exact_return_checks": return_checks,
        "all_exact_minimum_return_checks_pass": all(return_checks.values()),
        "location_reports_against_independent_minimum": reports,
        "maximum_endpoint_guessed": False,
        "resonance_width_law_or_bit7_role_confirmed": False,
        "resonance_writer_enabled": False,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["source_artifact"]
    observation_path = (
        root / "experiments/event-062-a-sound3-filter-B-lock-down/hardware-observation-001.json"
    )
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    captures = [directory / "capture.wav" for directory in directories]
    paths = [directory / "derived/analysis-001/capture.symbols.npz" for directory in directories]
    output = root / "experiments/sound3-filter-B-range-results-001.json"
    validate_outputs([output], [registration_path, source_path, *captures, *paths], False)
    recorded = [load_artifact(path) for path in paths]
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
        or sha256_file(observation_path) != registration["source_observation_sha256"]
        or sha256_file(observation_path.parent / "B-probe-results-001.json")
        != registration["source_results_sha256"]
        or any(
            item.metadata["source_sha256"] != sha256_file(capture)
            for item, capture in zip(recorded, captures)
        )
    ):
        raise ValueError("Registered B minimum or independent capture identity differs")
    frames = [decode_artifact(item) for item in recorded]
    report = B_range_report(decode_artifact(load_artifact(source_path)), *frames, registration)
    report.update(
        analysis_version="recorded-FILTER-B-maximum-and-exact-minimum-return-check-0.1",
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
        or not report["both_actual_native_controls_pass"]
    ):
        raise ValueError("FILTER B native range control failed; report retained")


if __name__ == "__main__":
    main()
