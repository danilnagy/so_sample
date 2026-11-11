"""Check fixed FILTER scope and complete clockwise return without endpoint fitting."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_probe import recorded_report
from scripts.prepare_sound3_filter_range import CAPTURE_IDS, REGISTRATION


def alternative_values(frame):
    data = pattern_data(frame, 1)
    return [((data[48 * step + 7] >> 4) << 2) | (data[48 * step + 8] & 3) for step in range(16)]


def mask_preserved(base, actual):
    a, b = [bytearray(pattern_data(frame, 1)) for frame in (base, actual)]
    for step in range(16):
        for data in (a, b):
            data[48 * step + 7] &= 15
            data[48 * step + 8] &= 252
    return a == b


def range_report(base, counterclockwise, returned, registration):
    reports = [recorded_report(base, frame, registration) for frame in (counterclockwise, returned)]
    scope = all(all(report["preservation_checks"].values()) for report in reports)
    return_checks = {
        "entire_return_body_matches_registered_clockwise": hashlib.sha256(
            returned.encoded_body
        ).hexdigest()
        == registration["expected_capture_sequence"][1]["expected_complete_body_sha256"],
        "entire_return_body_and_packets_equal_independent_clockwise": returned.encoded_body
        == base.encoded_body
        and returned.packets == base.packets,
        "all16_contiguous_return_values_match_registered62": reports[1]["raw_Sound3_fields"][
            "after"
        ]["uninterpreted_candidate_values"]
        == registration["expected_capture_sequence"][1]["expected_contiguous_values"],
        "all16_alternative_return_values_match_registered59": alternative_values(returned)
        == registration["expected_capture_sequence"][1]["expected_alternative_values"],
    }
    values = reports[0]["raw_Sound3_fields"]["after"]["uninterpreted_candidate_values"]
    return {
        "source_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "both_actual_native_controls_pass": all(
            all(report["native_checks"].values()) for report in reports
        ),
        "all_non_target_state_preserved": scope,
        "strict_candidate_mask_preserved_in_both_legs": scope
        and all(mask_preserved(base, frame) for frame in (counterclockwise, returned)),
        "pitch14_and_volume36_preserved": all(
            report["raw_Sound3_fields"]["after"]["first_low5_values"]
            == registration["expected_pitch_values"]
            and report["raw_Sound3_fields"]["after"]["volume_values"]
            == registration["expected_volume_values"]
            for report in reports
        ),
        "exact_return_checks": return_checks,
        "all_exact_return_checks_pass": all(return_checks.values()),
        "counterclockwise_candidate_changes": bool(reports[0]["candidate_changed_steps"]),
        "counterclockwise_values_uniform": len(set(values)) == 1,
        "contiguous_values_by_leg": [
            report["raw_Sound3_fields"]["after"]["uninterpreted_candidate_values"]
            for report in reports
        ],
        "alternative_values_by_leg": [
            alternative_values(frame) for frame in (counterclockwise, returned)
        ],
        "location_reports_against_registered_clockwise": reports,
        "counterclockwise_endpoint_guessed": False,
        "filter_bit_order_width_or_Hz_scale_confirmed": False,
        "filter_writer_enabled": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, nargs=2)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["source_artifact"]
    observation_path = (
        root / "experiments/event-055-b-sound3-filter-A-lock-up/hardware-observation-001.json"
    )
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    paths = args.artifacts or [
        path / "derived/analysis-001/capture.symbols.npz" for path in directories
    ]
    captures = [path / "capture.wav" for path in directories]
    output = root / "experiments/sound3-filter-A-range-results-001.json"
    validate_outputs([output], [registration_path, source_path, *paths, *captures], False)
    recorded = [load_artifact(path) for path in paths]
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
        or sha256_file(observation_path) != registration["source_observation_sha256"]
        or any(
            item.metadata["source_sha256"] != sha256_file(capture)
            for item, capture in zip(recorded, captures)
        )
    ):
        raise ValueError("Registered FILTER clockwise or independent capture identity differs")
    base = decode_artifact(load_artifact(source_path))
    frames = [decode_artifact(item) for item in recorded]
    report = range_report(base, *frames, registration)
    report.update(
        analysis_version="recorded-FILTER-opposite-endpoint-and-exact-return-check-0.1",
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
        raise ValueError("FILTER native range control failed; report retained")


if __name__ == "__main__":
    main()
