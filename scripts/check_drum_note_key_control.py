"""Evaluate the recorded drum-key replacement separately from byte-value hypotheses."""

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
    begin, end = expected["primary_span"]
    auxiliary = expected["auxiliary_offset"]
    source_begin, source_end = expected["source_step1_primary_span"]
    source_auxiliary = expected["source_step1_auxiliary_offset"]
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packets = [i for i, (a, b) in enumerate(zip(base.packets, frame.packets)) if a != b]
    excluded = set(expected["pattern_packet_indices"])
    checks = {
        "packet_count": len(base.packets) == len(frame.packets) == expected["packet_count"],
        "frame_end_byte": base.end_byte == frame.end_byte == expected["frame_end_byte"],
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
        "baseline_pattern_identity": hashlib.sha256(before).hexdigest()
        == expected["baseline_pattern_sha256"],
        "baseline_target_pair_matches": before[begin:end].hex() == expected["baseline_primary_hex"]
        and before[auxiliary] == expected["baseline_auxiliary_byte"],
        "target_note_remains_populated": any(after[begin:end]) or after[auxiliary] != 0,
        "only_registered_drum_cell_bytes_changed": bool(changes)
        and all(c["offset"] in expected["allowed_pattern_byte_offsets"] for c in changes),
        "source_step1_key1_unchanged": before[source_begin:source_end]
        == after[source_begin:source_end]
        and before[source_auxiliary] == after[source_auxiliary],
        "all_melodic_cells_unchanged": all(
            before[48 * s : 48 * s + 24] == after[48 * s : 48 * s + 24]
            and before[768 + 16 * s : 768 + 16 * s + 8] == after[768 + 16 * s : 768 + 16 * s + 8]
            for s in range(16)
        ),
        "pattern_packet_locations_unchanged": pattern_groups(base)[0]
        == pattern_groups(frame)[0]
        == expected["pattern_packet_indices"],
        "sample_and_reference_packets_unchanged": tuple(
            p for p in base.packets if p.tag in (0x68B5, 0xEF78)
        )
        == tuple(p for p in frame.packets if p.tag in (0x68B5, 0xEF78)),
        "every_other_plain_packet_unchanged": tuple(
            p for i, p in enumerate(base.packets) if i not in excluded
        )
        == tuple(p for i, p in enumerate(frame.packets) if i not in excluded),
        "other15_patterns_unchanged": all(
            pattern_data(base, n) == pattern_data(frame, n) for n in range(2, 17)
        ),
        "footer_unchanged": before[1024:] == after[1024:],
    }
    hypotheses = registration["separately_evaluated_hypotheses"]
    fits = {
        "primary_remains_observed_drum_pair": after[begin:end].hex()
        == hypotheses["primary_remains_observed_drum_pair"]["expected_hex"],
        "auxiliary_preserves_drum_upper_nibble_and_increments_key": after[auxiliary]
        == hypotheses["auxiliary_preserves_drum_upper_nibble_and_increments_key"]["expected_value"],
        "auxiliary_matches_melodic_key2": after[auxiliary]
        == hypotheses["auxiliary_matches_melodic_key2"]["expected_value"],
        "only_auxiliary_byte_changes": changes
        == hypotheses["only_auxiliary_byte_changes"]["expected_byte_changes"],
        "only_auxiliary_packet_changes": packets
        == hypotheses["only_auxiliary_packet_changes"]["expected_changed_plain_packet_indices"],
    }
    observed = {
        "before_primary_hex": before[begin:end].hex(),
        "after_primary_hex": after[begin:end].hex(),
        "before_auxiliary_byte": before[auxiliary],
        "after_auxiliary_byte": after[auxiliary],
    }
    return checks, fits, packets, changes, observed


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-021-b-drum10-step9-key2"
    registration_path = root / "experiments/drum10-step9-key2-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    source_path = directory / registration["baseline_artifact"]
    baseline_capture = directory / registration["baseline_capture"]
    capture, actual_path = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    output = root / "experiments/drum10-step9-key2-results-001.json"
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
        raise ValueError("Baseline or key2 capture differs from registered source identity")
    checks, fits, packets, changes, observed = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "first-drum10-pattern-key2-check-0.1",
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
        "drum_key2_writer_enabled": False,
        "limits": registration["limits"],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Drum-key2 preservation failed; report retained")


if __name__ == "__main__":
    main()
