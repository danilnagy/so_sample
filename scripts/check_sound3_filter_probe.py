"""Keep no-change, strict FILTER and broader snapshot alternatives distinct."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_tone_lock_probe import pattern_cell_changes
from scripts.check_sound3_volume_probe import raw_changes
from scripts.prepare_sound3_filter_probe import CAPTURE_IDS, REGISTRATION


def selection_report(base, selected, registration):
    return {
        "source_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "both_native_bodies_reencode_exactly": all(
            encode_packets(frame.packets) == frame.encoded_body for frame in (base, selected)
        ),
        "expected_native_geometry": len(selected.packets) == registration["expected_packet_count"]
        and selected.end_byte == registration["expected_frame_end_byte"],
        "entire_selection_body_matches_prediction": hashlib.sha256(
            selected.encoded_body
        ).hexdigest()
        == registration["expected_capture_sequence"][0]["expected_complete_body_sha256"],
        "entire_selection_body_and_packets_unchanged": selected.encoded_body == base.encoded_body
        and selected.packets == base.packets,
    }


def recorded_report(selected, recorded, registration):
    if registration["candidate"] != {
        "pattern": 1,
        "sound": 3,
        "second_primary_mask": 240,
        "third_primary_mask": 3,
    } or registration["broader_FILTER_candidate"] != {
        "second_primary_mask": 240,
        "third_primary_mask": 255,
    }:
        raise ValueError("FILTER masks differ from fixed preregistered alternatives")
    before, after = pattern_data(selected, 1), pattern_data(recorded, 1)
    cells = pattern_cell_changes(before, after)
    preserve = {
        "all_non_pattern_packets_and_samples_unchanged": tuple(
            p for p in selected.packets if p.tag != 0xC498
        )
        == tuple(p for p in recorded.packets if p.tag != 0xC498),
        "other15_patterns_unchanged": all(
            pattern_data(selected, slot) == pattern_data(recorded, slot) for slot in range(2, 17)
        ),
        "packet_tags_and_lengths_unchanged": [(p.tag, len(p.payload)) for p in selected.packets]
        == [(p.tag, len(p.payload)) for p in recorded.packets],
        "pattern1_footer_unchanged": before[1024:] == after[1024:],
    }
    only_sound3 = (
        bool(cells) and all(cell["sound_slot"] == 3 for cell in cells) and all(preserve.values())
    )
    aux_exact = all(cell["auxiliary_before"] == cell["auxiliary_after"] for cell in cells)

    def masked_equal(second_mask, third_mask):
        a, b = bytearray(before), bytearray(after)
        for step in range(16):
            for data in (a, b):
                data[48 * step + 7] &= 255 ^ second_mask
                data[48 * step + 8] &= 255 ^ third_mask
        return a == b

    candidate_changes = [
        step + 1
        for step in range(16)
        if (before[48 * step + 7] & 240, before[48 * step + 8] & 3)
        != (after[48 * step + 7] & 240, after[48 * step + 8] & 3)
    ]
    candidate = registration["candidate"]
    broader = registration["broader_FILTER_candidate"]
    return {
        "native_checks": {
            "both_actual_bodies_reencode_exactly": all(
                encode_packets(frame.packets) == frame.encoded_body
                for frame in (selected, recorded)
            ),
            "expected_recorded_geometry": len(recorded.packets)
            == registration["expected_packet_count"]
            and recorded.end_byte == registration["expected_frame_end_byte"],
        },
        "preservation_checks": preserve,
        "actual_A_body_sha256_used_as_B_source": hashlib.sha256(selected.encoded_body).hexdigest(),
        "location_hypotheses": {
            "no_serialized_change": recorded.encoded_body == selected.encoded_body,
            "strict_candidate_mask_only": only_sound3
            and aux_exact
            and bool(candidate_changes)
            and masked_equal(candidate["second_primary_mask"], candidate["third_primary_mask"]),
            "candidate_plus_other_third_byte_bits": only_sound3
            and aux_exact
            and bool(candidate_changes)
            and masked_equal(broader["second_primary_mask"], broader["third_primary_mask"]),
            "other_Sound3_primary_changes": only_sound3 and aux_exact,
            "Sound3_primary_and_auxiliary_changes": only_sound3,
        },
        "candidate_changed_steps": candidate_changes,
        "changed_cells": cells,
        "raw_changes": raw_changes(selected, recorded),
        "raw_Sound3_fields": {
            name: {
                "first_low5_values": [data[48 * step + 6] & 31 for step in range(16)],
                "volume_values": [
                    (data[48 * step + 6] >> 6) | ((data[48 * step + 7] & 15) << 2)
                    for step in range(16)
                ],
                "uninterpreted_candidate_values": [
                    (data[48 * step + 7] >> 4) | ((data[48 * step + 8] & 3) << 4)
                    for step in range(16)
                ],
                "uninterpreted_third_high6_values": [
                    data[48 * step + 8] >> 2 for step in range(16)
                ],
                "primary_hex_by_step": [
                    data[48 * step + 6 : 48 * step + 9].hex() for step in range(16)
                ],
            }
            for name, data in (("before", before), ("after", after))
        },
        "filter_field_width_or_scale_confirmed": False,
        "uniform_endpoint_required": False,
        "filter_writer_enabled": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["source_artifact"]
    source = load_artifact(source_path)
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
    ):
        raise ValueError("Registered FILTER source identity differs")
    directories = [
        root / "experiments" / name for name in CAPTURE_IDS[: 1 if args.selection_only else 2]
    ]
    paths = [path / "derived/analysis-001/capture.symbols.npz" for path in directories]
    captures = [path / "capture.wav" for path in directories]
    output = (
        directories[0] / "selection-results-001.json"
        if args.selection_only
        else root / "experiments/sound3-filter-probe-results-001.json"
    )
    validate_outputs([output], [registration_path, source_path, *paths, *captures], False)
    recorded = [load_artifact(path) for path in paths]
    if any(
        item.metadata["source_sha256"] != sha256_file(capture)
        for item, capture in zip(recorded, captures)
    ):
        raise ValueError("Independent FILTER capture identity differs")
    base = decode_artifact(source)
    frames = [decode_artifact(item) for item in recorded]
    checks = selection_report(base, frames[0], registration)
    report = {
        "analysis_version": "FILTER-selection-and-recorded-A-check-0.1",
        "hardware_verified": False,
        "selection_checks": checks,
        "selection_prediction_passed": all(checks.values()),
        "selection_raw_changes": raw_changes(base, frames[0]),
        "registration_sha256": sha256_file(registration_path),
        "captures": [
            {
                "experiment_id": path.name,
                "capture_sha256": sha256_file(capture),
                "artifact_sha256": sha256_file(artifact),
                "artifact_path": artifact.relative_to(root).as_posix(),
                "native_frame": frame_report(frame),
            }
            for path, capture, artifact, frame in zip(directories, captures, paths, frames)
        ],
        "limits": registration["limits"],
    }
    if not args.selection_only:
        report["recorded_B_against_actual_A"] = recorded_report(*frames, registration)
    write_bytes(output, json_bytes(report))
    if not all(
        checks[key]
        for key in (
            "source_body_matches_registration",
            "both_native_bodies_reencode_exactly",
            "expected_native_geometry",
        )
    ):
        raise ValueError("FILTER native control failed; report retained")
    if not args.selection_only and not all(
        report["recorded_B_against_actual_A"]["native_checks"].values()
    ):
        raise ValueError("Recorded FILTER native control failed; report retained")


if __name__ == "__main__":
    main()
