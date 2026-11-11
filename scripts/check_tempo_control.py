"""Report a controlled tempo change without enabling a tempo writer or fitting offsets."""

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


def comparison_checks(base, actual, registration, before_bpm=None, after_bpm=None):
    for value in (before_bpm, after_bpm):
        if value is not None and (type(value) is not int or not 60 <= value <= 240):
            raise ValueError("Observed display BPM must be an integer from60 to240")
    before, after = grouped_packets(base), grouped_packets(actual)
    old_globals = [p.payload for p in base.packets if p.tag == 0x7D5C]
    new_globals = [p.payload for p in actual.packets if p.tag == 0x7D5C]
    checks = {
        "baseline_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["baseline_body_sha256"],
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
        "selector_order_unchanged": list(before) == list(after),
        "all_sample_records_unchanged": before == after,
        "all_patterns_unchanged": all(
            pattern_data(base, n) == pattern_data(actual, n) for n in range(1, 17)
        ),
    }
    candidate = registration["candidate"]
    occurrence, offset = (
        candidate["occurrence_index_zero_based"],
        candidate["payload_offset_zero_based"],
    )
    old = old_globals[occurrence] if len(old_globals) > occurrence else b""
    new = new_globals[occurrence] if len(new_globals) > occurrence else b""
    changed = [i for i, (a, b) in enumerate(zip_longest(old, new)) if a != b]
    expected_globals = len(old_globals) == len(new_globals) == 2 and all(
        len(raw) == 255 for raw in old_globals + new_globals
    )
    fits = {
        "native_body_changed": actual.encoded_body != base.encoded_body,
        "same_packet_tags_and_lengths": [(p.tag, len(p.payload)) for p in base.packets]
        == [(p.tag, len(p.payload)) for p in actual.packets],
        "all_non_global_packets_unchanged": tuple(p for p in base.packets if p.tag != 0x7D5C)
        == tuple(p for p in actual.packets if p.tag != 0x7D5C),
        "two_global_records_keep_observed_sizes": expected_globals,
        "first_global_record_unchanged": bool(old_globals and new_globals)
        and old_globals[0] == new_globals[0],
        "only_registered_candidate_byte_changed": changed == [offset],
        "baseline_candidate_matches_observed_before_BPM": old[offset] == before_bpm
        if before_bpm is not None and len(old) > offset
        else None,
        "candidate_matches_observed_after_BPM": new[offset] == after_bpm
        if after_bpm is not None and len(new) > offset
        else None,
    }
    numerical_evidence = before_bpm is not None and after_bpm is not None
    support_checks = [fits[key] for key in fits if key != "native_body_changed"]
    status = (
        "not_evaluated_without_display_observations"
        if not numerical_evidence
        else "supported_for_this_transition"
        if all(checks.values()) and all(support_checks) and before_bpm != after_bpm
        else "not_supported_for_this_transition"
    )
    differences = []
    for index, (left, right) in enumerate(zip_longest(base.packets, actual.packets)):
        if left == right:
            continue
        item = {
            "packet_index_zero_based": index,
            "before_tag": f"0x{left.tag:04x}" if left else None,
            "after_tag": f"0x{right.tag:04x}" if right else None,
        }
        if left and right:
            item.update(
                before_payload_bytes=len(left.payload),
                after_payload_bytes=len(right.payload),
                changed_payload_bytes=[
                    {"offset_zero_based": i, "before": a, "after": b}
                    for i, (a, b) in enumerate(zip_longest(left.payload, right.payload))
                    if a != b
                ],
            )
        differences.append(item)
    observed = {
        "display_before_bpm": before_bpm,
        "display_after_bpm": after_bpm,
        "candidate_before": old[offset] if len(old) > offset else None,
        "candidate_after": new[offset] if len(new) > offset else None,
        "candidate_changed_offsets": changed,
        "single_byte_hypothesis_status": status,
        "changed_packets": differences,
    }
    return checks, fits, observed


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument(
        "--experiment-dir", type=Path, default=root / "experiments/event-030-b-tempo-preset-once"
    )
    parser.add_argument("--before-bpm", type=int)
    parser.add_argument("--after-bpm", type=int)
    args = parser.parse_args()
    directory = args.experiment_dir
    artifact_path = args.artifact or directory / "derived/analysis-001/capture.symbols.npz"
    registration_path = directory / "tempo-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["baseline_artifact"]
    capture = directory / "capture.wav"
    output = directory / "native-tempo-results-001.json"
    validate_outputs([output], [registration_path, source_path, capture, artifact_path], False)
    source, recorded = load_artifact(source_path), load_artifact(artifact_path)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(root / registration["baseline_capture"])
        != registration["baseline_capture_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Registered source or capture identity differs")
    base, actual = decode_artifact(source), decode_artifact(recorded)
    checks, fits, observed = comparison_checks(
        base, actual, registration, args.before_bpm, args.after_bpm
    )
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "single-BPM-button-tempo-control-check-0.1",
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": sha256_file(capture),
                "artifact_sha256": sha256_file(artifact_path),
                "control_checks": checks,
                "control_passed": all(checks.values()),
                "hypothesis_checks": fits,
                "observed_change": observed,
                "native_frame": frame_report(actual),
                "tempo_writer_enabled": False,
                "limits": registration["limits"],
            }
        ),
    )
    if not all(checks.values()):
        raise ValueError(
            "Tempo control changed samples, patterns or other core invariants; report retained"
        )


if __name__ == "__main__":
    main()
