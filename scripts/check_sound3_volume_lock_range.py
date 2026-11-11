"""Evaluate preregistered low-nibble minimum and exact recorded-maximum return."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import grouped_packets
from scripts.check_sound3_volume_probe import raw_changes
from scripts.prepare_sound3_volume_lock_range import CAPTURE_IDS


def masked_pattern(data, offsets):
    masked = bytearray(data)
    for offset in offsets:
        masked[offset] &= 0xF0
    return bytes(masked)


def comparison_checks(before, after, offsets):
    return {
        "all_sample_records_and_codes_unchanged": grouped_packets(before) == grouped_packets(after),
        "all_non_pattern_packets_unchanged": tuple(p for p in before.packets if p.tag != 0xC498)
        == tuple(p for p in after.packets if p.tag != 0xC498),
        "other15_patterns_unchanged": all(
            pattern_data(before, slot) == pattern_data(after, slot) for slot in range(2, 17)
        ),
        "all_pattern1_bits_except_candidate_low_nibbles_unchanged": masked_pattern(
            pattern_data(before, 1), offsets
        )
        == masked_pattern(pattern_data(after, 1), offsets),
        "packet_tags_and_lengths_unchanged": [(p.tag, len(p.payload)) for p in before.packets]
        == [(p.tag, len(p.payload)) for p in after.packets],
        "tempo100_and_swing9_preserved": after.packets[2].tag == 0x7D5C
        and after.packets[2].payload[129:131] == bytes([100, 9]),
    }


def range_checks(base, minimum, returned, registration):
    offsets = registration["candidate"]["concatenated_pattern_payload_offsets_zero_based"]
    if offsets != [48 * step + 7 for step in range(16)]:
        raise ValueError("Exactly the preregistered16 Sound3 second-byte low nibbles required")
    controls = {
        "original_maximum_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["baseline_body_sha256"],
        "both_actual_native_bodies_reencode_exactly": all(
            encode_packets(frame.packets) == frame.encoded_body for frame in (minimum, returned)
        ),
    }
    preservation = [
        comparison_checks(a, b, offsets) for a, b in ((base, minimum), (minimum, returned))
    ]
    raw_values = [
        [pattern_data(frame, 1)[offset] & 15 for offset in offsets]
        for frame in (base, minimum, returned)
    ]
    hypotheses = {
        "original_maximum_all16_raw_nibbles_f": raw_values[0] == [15] * 16,
        "minimum_all16_raw_nibbles_zero": raw_values[1] == [0] * 16,
        "return_all16_raw_nibbles_f": raw_values[2] == [15] * 16,
        "minimum_entire_body_matches_prediction": hashlib.sha256(minimum.encoded_body).hexdigest()
        == registration["expected_capture_sequence"][0]["expected_body_sha256"],
        "return_entire_body_matches_prediction": hashlib.sha256(returned.encoded_body).hexdigest()
        == registration["expected_capture_sequence"][1]["expected_body_sha256"],
        "complete_return_body_equals_independent_original_maximum": returned.encoded_body
        == base.encoded_body,
        "complete_return_packets_equal_independent_original_maximum": returned.packets
        == base.packets,
    }
    supported = (
        all(controls.values())
        and all(all(leg.values()) for leg in preservation)
        and all(hypotheses.values())
    )
    return {
        "control_checks": controls,
        "control_passed": all(controls.values()),
        "minimum_preservation_checks": preservation[0],
        "return_preservation_checks": preservation[1],
        "hypothesis_checks": hypotheses,
        "low_nibble_minimum_and_exact_return_supported": supported,
        "original_maximum_raw_nibbles": raw_values[0],
        "actual_minimum_raw_nibbles": raw_values[1],
        "actual_return_raw_nibbles": raw_values[2],
        "minimum_raw_changes": raw_changes(base, minimum),
        "return_raw_changes": raw_changes(minimum, returned),
        "numeric_display_values_inferred": False,
        "gain_scale_or_mute_behavior_confirmed": False,
        "volume_writer_enabled": False,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, nargs=2)
    parser.add_argument("--minimum-display-text")
    parser.add_argument("--maximum-display-text")
    args = parser.parse_args()
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    captures = [directory / "capture.wav" for directory in directories]
    paths = args.artifacts or [
        directory / "derived/analysis-001/capture.symbols.npz" for directory in directories
    ]
    registration_path = root / "experiments/sound3-volume-lock-range-registration-001.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["baseline_artifact"]
    output = root / "experiments/sound3-volume-lock-range-results-001.json"
    validate_outputs([output], [registration_path, source_path, *captures, *paths], False)
    recorded = [load_artifact(path) for path in paths]
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(root / registration["baseline_capture"])
        != registration["baseline_capture_sha256"]
        or any(
            item.metadata["source_sha256"] != sha256_file(capture)
            for item, capture in zip(recorded, captures)
        )
    ):
        raise ValueError("Registered source or volume minimum/return capture identity differs")
    base = decode_artifact(load_artifact(source_path))
    frames = [decode_artifact(item) for item in recorded]
    report = range_checks(base, *frames, registration)
    report.update(
        analysis_version="sound3-recorded-volume-low-nibble-range-check-0.1",
        hardware_verified=False,
        registration_sha256=sha256_file(registration_path),
        independently_reported_minimum_display_text=args.minimum_display_text,
        independently_reported_maximum_display_text=args.maximum_display_text,
        captures=[
            {
                "experiment_id": directory.name,
                "capture_sha256": sha256_file(capture),
                "artifact_sha256": sha256_file(path),
                "artifact_path": str(path),
                "native_frame": frame_report(frame),
            }
            for directory, capture, path, frame in zip(directories, captures, paths, frames)
        ],
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Volume range source or native control failed; report retained")


if __name__ == "__main__":
    main()
