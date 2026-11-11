"""Retain competing recorded-pitch location hypotheses without refitting their masks."""

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
from scripts.prepare_sound3_tone_pitch_probe import CAPTURE_ID, REGISTRATION


def location_report(base, actual, registration):
    before, after = pattern_data(base, 1), pattern_data(actual, 1)
    cells = pattern_cell_changes(before, after)
    preservation = {
        "all_non_pattern_packets_and_sample_data_unchanged": tuple(
            p for p in base.packets if p.tag != 0xC498
        )
        == tuple(p for p in actual.packets if p.tag != 0xC498),
        "other15_patterns_unchanged": all(
            pattern_data(base, slot) == pattern_data(actual, slot) for slot in range(2, 17)
        ),
        "packet_tags_and_lengths_unchanged": [(p.tag, len(p.payload)) for p in base.packets]
        == [(p.tag, len(p.payload)) for p in actual.packets],
        "pattern1_footer_unchanged": before[1024:] == after[1024:],
        "tempo100_and_swing9_preserved": actual.packets[2].tag == 0x7D5C
        and actual.packets[2].payload[129:131]
        == bytes([registration["expected_tempo_bpm"], registration["expected_swing_byte"]]),
    }
    sound3_only = (
        bool(cells)
        and all(cell["sound_slot"] == 3 for cell in cells)
        and all(preservation.values())
    )
    aux_exact = all(cell["auxiliary_before"] == cell["auxiliary_after"] for cell in cells)
    pitch_changes = [
        step + 1
        for step in range(16)
        if (before[48 * step + 6] & 63) != (after[48 * step + 6] & 63)
    ]

    def masked_equal(first_mask, second_mask):
        a, b = bytearray(before), bytearray(after)
        for step in range(16):
            for data in (a, b):
                data[48 * step + 6] &= 255 ^ first_mask
                data[48 * step + 7] &= 255 ^ second_mask
        return a == b

    control = {
        "source_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "both_native_bodies_reencode_exactly": all(
            encode_packets(frame.packets) == frame.encoded_body for frame in (base, actual)
        ),
        "expected_native_geometry": len(actual.packets) == registration["expected_packet_count"]
        and actual.end_byte == registration["expected_frame_end_byte"],
    }
    return {
        "control_checks": control,
        "control_passed": all(control.values()),
        "preservation_checks": preservation,
        "location_hypotheses": {
            "no_serialized_change": actual.encoded_body == base.encoded_body,
            "strict_pitch_candidate_only": sound3_only
            and aux_exact
            and bool(pitch_changes)
            and masked_equal(63, 0),
            "pitch_candidate_plus_known_volume": sound3_only
            and aux_exact
            and bool(pitch_changes)
            and masked_equal(255, 15),
            "other_sound3_primary_changes": sound3_only and aux_exact,
            "sound3_primary_and_auxiliary_changes": sound3_only,
        },
        "first_low6_changed_steps": pitch_changes,
        "raw_sound3_fields": {
            name: {
                "first_primary_low6_values": [data[48 * step + 6] & 63 for step in range(16)],
                "known_volume_values": [
                    (data[48 * step + 6] >> 6) | ((data[48 * step + 7] & 15) << 2)
                    for step in range(16)
                ],
                "primary_hex_by_step": [
                    data[48 * step + 6 : 48 * step + 9].hex() for step in range(16)
                ],
                "auxiliary_values": [data[768 + 16 * step + 2] for step in range(16)],
            }
            for name, data in (("before", before), ("after", after))
        },
        "pattern1_changed_cells": cells,
        "raw_changes": raw_changes(base, actual),
        "raw_endpoint_numeric_value_assumed": None,
        "pitch_scale_confirmed": False,
        "uniform_endpoint_required": False,
        "pitch_field_writer_enabled": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--display-text")
    parser.add_argument("--audition-result", choices=("lower", "higher", "unchanged", "unknown"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    directory = root / "experiments" / CAPTURE_ID
    source_path = root / registration["source_artifact"]
    capture_path = directory / "capture.wav"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    observation_path = (
        root / "experiments/event-050-a-sound3-volume36-post-playback/hardware-observation-001.json"
    )
    output = directory / "pitch-probe-results-001.json"
    validate_outputs([output], [registration_path, source_path, capture_path, artifact_path], False)
    recorded = load_artifact(artifact_path)
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
        or sha256_file(observation_path) != registration["source_observation_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture_path)
    ):
        raise ValueError("Registered baseline or independent capture identity differs")
    base, actual = [decode_artifact(item) for item in (load_artifact(source_path), recorded)]
    report = location_report(base, actual, registration)
    report.update(
        analysis_version="recorded-TONE-A-down-location-hypotheses-0.1",
        hardware_verified=False,
        registration_sha256=sha256_file(registration_path),
        capture_sha256=sha256_file(capture_path),
        artifact_sha256=sha256_file(artifact_path),
        artifact_path=artifact_path.relative_to(root).as_posix(),
        native_frame=frame_report(actual),
        independently_reported_display_text=args.display_text,
        independently_reported_audition_result=args.audition_result,
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Native control failed; pitch-probe report retained")


if __name__ == "__main__":
    main()
