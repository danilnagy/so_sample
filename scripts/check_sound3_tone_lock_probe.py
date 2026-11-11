"""Observe plain playback and recorded TONE cells without inferring parameter bitfields."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import grouped_packets
from scripts.check_sound3_volume_probe import preservation_checks, raw_changes
from scripts.prepare_sound3_tone_lock_probe import CAPTURE_IDS


def pattern_cell_changes(before, after):
    changes = []
    for step in range(16):
        for sound in range(16):
            p, a = 48 * step + 3 * sound, 768 + 16 * step + sound
            old, new = before[p : p + 3], after[p : p + 3]
            if old != new or before[a] != after[a]:
                changes.append(
                    {
                        "step": step + 1,
                        "sound_slot": sound + 1,
                        "primary_before_hex": old.hex(),
                        "primary_after_hex": new.hex(),
                        "auxiliary_before": before[a],
                        "auxiliary_after": after[a],
                        "previously_completely_empty_cell": old == bytes(3) and before[a] == 0,
                    }
                )
    return changes


def probe_checks(base, playback, locked, registration):
    before, after = pattern_data(playback, 1), pattern_data(locked, 1)
    cells = pattern_cell_changes(before, after)
    a_checks = preservation_checks(base, playback, registration)
    b_checks = {
        "all_sample_records_and_codes_unchanged": grouped_packets(playback)
        == grouped_packets(locked),
        "other15_patterns_unchanged": all(
            pattern_data(playback, slot) == pattern_data(locked, slot) for slot in range(2, 17)
        ),
        "all_non_pattern_packets_unchanged": tuple(p for p in playback.packets if p.tag != 0xC498)
        == tuple(p for p in locked.packets if p.tag != 0xC498),
        "tempo100_and_swing9_preserved": locked.packets[2].tag == 0x7D5C
        and locked.packets[2].payload[129:131]
        == bytes([registration["expected_tempo_bpm"], registration["expected_swing_byte"]]),
        "all_packet_tags_and_lengths_preserved": [(p.tag, len(p.payload)) for p in playback.packets]
        == [(p.tag, len(p.payload)) for p in locked.packets],
        "pattern1_footer_unchanged": before[1024:] == after[1024:],
    }
    only_sound3 = (
        bool(cells) and all(cell["sound_slot"] == 3 for cell in cells) and all(b_checks.values())
    )
    core = {
        "baseline_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["baseline_body_sha256"],
        "both_native_bodies_reencode_exactly": all(
            encode_packets(frame.packets) == frame.encoded_body for frame in (playback, locked)
        ),
    }
    return {
        "control_checks": core,
        "control_passed": all(core.values()),
        "plain_playback_preservation_checks": a_checks,
        "lock_preservation_checks": b_checks,
        "plain_playback_body_matches_preregistered_prediction": hashlib.sha256(
            playback.encoded_body
        ).hexdigest()
        == registration["expected_capture_sequence"][0][
            "expected_body_sha256_if_plain_playback_is_not_serialized"
        ],
        "location_hypotheses": {
            "tone_lock_no_serialized_change": locked.encoded_body == playback.encoded_body,
            "tone_lock_only_pattern1_sound3_primary_cells_changed": only_sound3
            and all(cell["auxiliary_before"] == cell["auxiliary_after"] for cell in cells),
            "tone_lock_only_pattern1_sound3_primary_and_auxiliary_cells_changed": only_sound3,
        },
        "pattern1_changed_cells_against_actual_playbackA": cells,
        "plain_playback_raw_changes_against_prior_baseline": raw_changes(base, playback),
        "lock_raw_changes_against_actual_playbackA": raw_changes(playback, locked),
        "volume_specific_bitfield_confirmed": False,
        "maximum_numeric_value_inferred": False,
        "volume_writer_enabled": False,
        "pitch_field_writer_enabled": False,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, nargs=2)
    parser.add_argument("--display-text")
    parser.add_argument("--audition-result", choices=("louder", "unchanged", "quieter", "unknown"))
    args = parser.parse_args()
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    captures = [directory / "capture.wav" for directory in directories]
    paths = args.artifacts or [
        directory / "derived/analysis-001/capture.symbols.npz" for directory in directories
    ]
    registration_path = root / "experiments/sound3-tone-lock-probe-registration-001.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["baseline_artifact"]
    output = root / "experiments/sound3-tone-lock-probe-results-001.json"
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
        raise ValueError("Registered live-volume source or playback/lock capture identity differs")
    base = decode_artifact(load_artifact(source_path))
    frames = [decode_artifact(item) for item in recorded]
    report = probe_checks(base, *frames, registration)
    report.update(
        analysis_version="sound3-plain-playback-and-tone-lock-observation-0.1",
        hardware_verified=False,
        registration_sha256=sha256_file(registration_path),
        independently_reported_display_text=args.display_text,
        independently_reported_audition_result=args.audition_result,
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
        raise ValueError("Native source/control checks failed; tone-lock report retained")


if __name__ == "__main__":
    main()
