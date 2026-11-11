"""Check preregistered pitch masks and complete minimum return without endpoint fitting."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_tone_pitch_probe import location_report
from scripts.prepare_sound3_tone_pitch_range import CAPTURE_IDS, REGISTRATION


def first_mask_preserved(before, after, mask):
    a, b = [bytearray(pattern_data(frame, 1)) for frame in (before, after)]
    for step in range(16):
        a[48 * step + 6] &= 255 ^ mask
        b[48 * step + 6] &= 255 ^ mask
    return a == b


def range_report(base, maximum, returned, registration):
    reports = [location_report(base, frame, registration) for frame in (maximum, returned)]
    all_state_preserved = all(all(report["preservation_checks"].values()) for report in reports)
    masks = {
        "only_first_low6_bits_changed_in_both_legs": all_state_preserved
        and all(first_mask_preserved(base, frame, 63) for frame in (maximum, returned)),
        "only_first_low5_bits_changed_in_both_legs": all_state_preserved
        and all(first_mask_preserved(base, frame, 31) for frame in (maximum, returned)),
    }
    return_checks = {
        "entire_return_body_matches_registered_minimum": hashlib.sha256(
            returned.encoded_body
        ).hexdigest()
        == registration["expected_capture_sequence"][1]["expected_complete_body_sha256"],
        "entire_return_body_and_packets_equal_independent_minimum": returned.encoded_body
        == base.encoded_body
        and returned.packets == base.packets,
        "all16_return_candidate_values_equal_registered1": reports[1]["raw_sound3_fields"]["after"][
            "first_primary_low6_values"
        ]
        == [registration["expected_capture_sequence"][1]["expected_endpoint_code"]] * 16,
    }
    upper = reports[0]["raw_sound3_fields"]["after"]["first_primary_low6_values"]
    volume = [report["raw_sound3_fields"]["after"]["known_volume_values"] for report in reports]
    return {
        "control_passed": all(report["control_passed"] for report in reports),
        "all_non_target_state_preserved": all_state_preserved,
        "location_reports_against_registered_minimum": reports,
        "mask_hypotheses": masks,
        "exact_return_checks": return_checks,
        "all_exact_return_checks_pass": all(return_checks.values()),
        "volume36_preserved_in_both_legs": all(
            values == registration["expected_volume_values"] for values in volume
        ),
        "maximum_changes_candidate_bits": bool(reports[0]["first_low6_changed_steps"]),
        "maximum_values_uniform": len(set(upper)) == 1,
        "maximum_first_low6_values_by_step": upper,
        "maximum_endpoint_value_guessed": False,
        "pitch_scale_or_field_width_confirmed": False,
        "pitch_field_writer_enabled": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, nargs=2)
    parser.add_argument("--maximum-display-text")
    parser.add_argument("--return-display-text")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    paths = args.artifacts or [
        path / "derived/analysis-001/capture.symbols.npz" for path in directories
    ]
    captures = [path / "capture.wav" for path in directories]
    source_path = root / registration["source_artifact"]
    observation_path = (
        root / "experiments/event-051-b-sound3-tone-pitch-lock-down/hardware-observation-001.json"
    )
    output = root / "experiments/sound3-tone-pitch-range-results-001.json"
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
        raise ValueError("Registered minimum or independent range capture identity differs")
    base = decode_artifact(load_artifact(source_path))
    frames = [decode_artifact(item) for item in recorded]
    report = range_report(base, *frames, registration)
    report.update(
        analysis_version="recorded-pitch-upper-and-exact-minimum-return-check-0.1",
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
        independently_reported_display_texts=[args.maximum_display_text, args.return_display_text],
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Native control failed; pitch-range report retained")


if __name__ == "__main__":
    main()
