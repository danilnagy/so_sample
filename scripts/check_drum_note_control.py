"""Check a physical drum-note addition without assuming its raw key encoding."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data, pattern_groups
from po33_re.modem.symbols import load_artifact


def comparison_checks(base, frame, registration):
    expected = registration["control_checks"]
    before, after = pattern_data(base, 1), pattern_data(frame, 1)
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packets = [i for i, (a, b) in enumerate(zip(base.packets, frame.packets)) if a != b]
    p_begin, p_end = expected["allowed_step_primary_span"]
    a_begin, a_end = expected["allowed_step_auxiliary_span"]
    allowed = {*range(p_begin, p_end), *range(a_begin, a_end)}
    neighbor_begin, neighbor_end = expected["existing_neighbor_primary_span"]
    neighbor_auxiliary = expected["existing_neighbor_auxiliary_offset"]
    cells = sorted(
        {
            (c["offset"] - p_begin) // 3 + 1
            if p_begin <= c["offset"] < p_end
            else c["offset"] - a_begin + 1
            for c in changes
            if c["offset"] in allowed
        }
    )
    one_empty = len(cells) == 1
    if one_empty:
        key = cells[0] - 1
        one_empty = (
            before[p_begin + 3 * key : p_begin + 3 * key + 3] == bytes(3)
            and before[a_begin + key] == 0
        )
    candidate_begin, candidate_end = expected["candidate_primary_span"]
    candidate_auxiliary = expected["candidate_auxiliary_offset"]
    excluded = set(expected["target_pattern_packet_indices"])
    checks = {
        "packet_count": len(base.packets) == len(frame.packets) == expected["packet_count"],
        "frame_end_byte": base.end_byte == frame.end_byte == expected["frame_end_byte"],
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
        "baseline_pattern_identity": hashlib.sha256(before).hexdigest()
        == expected["baseline_pattern1_sha256"],
        "baseline_candidate_cell_empty": before[candidate_begin:candidate_end] == bytes(3)
        and before[candidate_auxiliary] == 0,
        "pattern_packet_locations_unchanged": pattern_groups(base)[0]
        == pattern_groups(frame)[0]
        == expected["target_pattern_packet_indices"],
        "one_previously_empty_raw_step1_cell_changed": one_empty,
        "only_step1_primary_and_auxiliary_rows_changed": bool(changes)
        and all(c["offset"] in allowed for c in changes),
        "existing_melodic_neighbor_preserved": before[neighbor_begin:neighbor_end]
        == after[neighbor_begin:neighbor_end]
        and before[neighbor_auxiliary] == after[neighbor_auxiliary],
        "every_other_plain_packet_unchanged": tuple(
            p for i, p in enumerate(base.packets) if i not in excluded
        )
        == tuple(p for i, p in enumerate(frame.packets) if i not in excluded),
        "all_sample_and_reference_packets_unchanged": tuple(
            p for p in base.packets if p.tag in (0x68B5, 0xEF78)
        )
        == tuple(p for p in frame.packets if p.tag in (0x68B5, 0xEF78)),
        "other15_patterns_unchanged": all(
            pattern_data(base, n) == pattern_data(frame, n) for n in range(2, 17)
        ),
        "footer_unchanged": before[1024:] == after[1024:],
    }
    hypotheses = registration["separately_evaluated_hypotheses"]
    auxiliary = hypotheses["auxiliary_key1_matches_melodic_F0"]
    fits = {
        "sound10_maps_to_cell10": cells
        == hypotheses["sound10_maps_to_cell10"]["expected_changed_sound_cells"],
        "auxiliary_key1_matches_melodic_F0": before[auxiliary["offset"]] == auxiliary["old_value"]
        and after[auxiliary["offset"]] == auxiliary["expected_value"],
        "changed_plain_packet_indices": packets == hypotheses["changed_plain_packet_indices"],
    }
    for name in ("primary_matches_sound3_key1", "primary_matches_sound2_key1"):
        begin, end = hypotheses[name]["span"]
        fits[name] = after[begin:end].hex() == hypotheses[name]["expected_hex"]
    observed = {
        "candidate_primary_hex": after[candidate_begin:candidate_end].hex(),
        "candidate_auxiliary_byte": after[candidate_auxiliary],
        "changed_raw_sound_cells": cells,
    }
    return checks, fits, packets, changes, observed


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-020-b-drum10-key1-step1"
    registration_path = root / "experiments/drum10-note-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    source_path = directory / registration["baseline_artifact"]
    baseline_capture = directory / registration["baseline_capture"]
    capture, actual_path = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    output = root / "experiments/drum10-note-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, baseline_capture, capture, actual_path], False
    )
    source, recorded = load_artifact(source_path), load_artifact(actual_path)
    base, frame = decode_artifact(source), decode_artifact(recorded)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(baseline_capture) != registration["baseline_source_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Baseline or drum-note capture differs from registered source identity")
    checks, fits, packets, changes, observed = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "first-drum10-note-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(actual_path),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "changed_plain_packet_indices": packets,
        "pattern1_byte_changes": changes,
        "observed_note": observed,
        "native_frame": frame_report(frame),
        "drum_pattern_writer_enabled": False,
        "limits": registration["limits"],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Drum-note preservation control failed; report retained")


if __name__ == "__main__":
    main()
