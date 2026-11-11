"""Compare fresh Sound3 selection and volume controls without choosing a field afterward."""

import argparse
import hashlib
import json
from itertools import zip_longest
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import grouped_packets
from scripts.prepare_sound3_volume_probe import CAPTURE_IDS


def raw_changes(before, after):
    changes = []
    for index, (a, b) in enumerate(zip_longest(before.packets, after.packets)):
        if a == b:
            continue
        changes.append(
            {
                "packet_index_zero_based": index,
                "before_tag": f"0x{a.tag:04x}" if a else None,
                "after_tag": f"0x{b.tag:04x}" if b else None,
                "before_payload_bytes": len(a.payload) if a else None,
                "after_payload_bytes": len(b.payload) if b else None,
                "changed_payload_bytes": [
                    {"offset_zero_based": offset, "before": x, "after": y}
                    for offset, (x, y) in enumerate(
                        zip_longest(a.payload if a else b"", b.payload if b else b"")
                    )
                    if x != y
                ],
            }
        )
    return changes


def preservation_checks(before, after, registration):
    expected = bytes([registration["expected_tempo_bpm"], registration["expected_swing_byte"]])
    globals_after = [packet.payload for packet in after.packets if packet.tag == 0x7D5C]
    return {
        "all_sample_records_and_codes_unchanged": grouped_packets(before) == grouped_packets(after),
        "all16_patterns_unchanged": all(
            pattern_data(before, slot) == pattern_data(after, slot) for slot in range(1, 17)
        ),
        "tempo100_and_swing9_preserved": len(globals_after) == 2
        and globals_after[1][129:131] == expected,
        "all_packet_tags_and_lengths_preserved": [(p.tag, len(p.payload)) for p in before.packets]
        == [(p.tag, len(p.payload)) for p in after.packets],
    }


def probe_checks(base, selection, minimum, registration):
    controls = {
        "original_baseline_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["baseline_body_sha256"],
        "selection_complete_body_reencodes_exactly": encode_packets(selection.packets)
        == selection.encoded_body,
        "minimum_complete_body_reencodes_exactly": encode_packets(minimum.packets)
        == minimum.encoded_body,
    }
    selection_preserved = preservation_checks(base, selection, registration)
    minimum_preserved = preservation_checks(selection, minimum, registration)
    a_changes, b_changes = raw_changes(base, selection), raw_changes(selection, minimum)
    hypotheses = {
        "selection_only_no_serialized_change": selection.encoded_body == base.encoded_body,
        "volume_no_serialized_change": minimum.encoded_body == selection.encoded_body,
        "volume_changes_only_global_packets": bool(b_changes)
        and all(change["before_tag"] == change["after_tag"] == "0x7d5c" for change in b_changes),
        "volume_changes_pattern_data": not minimum_preserved["all16_patterns_unchanged"],
        "volume_changes_sample_records": not minimum_preserved[
            "all_sample_records_and_codes_unchanged"
        ],
    }
    return {
        "control_checks": controls,
        "control_passed": all(controls.values()),
        "selection_preservation_checks": selection_preserved,
        "minimum_preservation_checks": minimum_preserved,
        "musical_state_preserved_except_unknown_live_parameter": all(selection_preserved.values())
        and all(minimum_preserved.values()),
        "location_hypotheses": hypotheses,
        "selection_changes_against_original_baseline": a_changes,
        "minimum_changes_against_actual_selectionA": b_changes,
        "minimum_display_value_inferred": False,
        "volume_writer_enabled": False,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, nargs=2)
    parser.add_argument("--display-text")
    parser.add_argument("--audition-result", choices=("silent", "quieter", "unchanged", "unknown"))
    args = parser.parse_args()
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    captures = [directory / "capture.wav" for directory in directories]
    paths = args.artifacts or [
        directory / "derived/analysis-001/capture.symbols.npz" for directory in directories
    ]
    registration_path = root / "experiments/sound3-tone-volume-probe-registration-001.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["baseline_artifact"]
    output = root / "experiments/sound3-tone-volume-probe-results-001.json"
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
        raise ValueError("Registered source or selection/volume capture identity differs")
    base = decode_artifact(load_artifact(source_path))
    frames = [decode_artifact(item) for item in recorded]
    report = probe_checks(base, *frames, registration)
    report.update(
        analysis_version="sound3-selection-and-minimum-tone-volume-observation-0.1",
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
        limits=registration["limits"]
        + [
            "An unchanged body alone cannot distinguish transient live parameters from an ineffective action; independent display/audition evidence matters"
        ],
    )
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Volume probe source or native control failed; report retained")


if __name__ == "__main__":
    main()
