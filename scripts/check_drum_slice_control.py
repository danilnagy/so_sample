"""Check one changed drum reference and evaluate mapping/minimum predictions separately."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, sound_groups
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import grouped_packets


def reference_comparison_checks(base, frame, registration):
    expected = registration["control_checks"]
    ids = expected["sound9_selector_ids"]
    groups_before, groups_after = sound_groups(base), sound_groups(frame)
    before, after = grouped_packets(base), grouped_packets(frame)
    changed = sorted(
        key for key in before.keys() | after.keys() if before.get(key) != after.get(key)
    )
    changed_packets = [i for i, (a, b) in enumerate(zip(base.packets, frame.packets)) if a != b]
    changes, values = [], None
    one = len(changed) == 1 and changed[0] in ids
    if one:
        selector = changed[0]
        old = b"".join(p.payload for p in before[selector])
        new = b"".join(p.payload for p in after[selector])
        changes = [
            {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(old, new)) if a != b
        ]
        if len(old) == len(new) == 9:
            values = {"selector_id": selector, "before_hex": old.hex(), "after_hex": new.hex()}
            for name, data in (("before", old), ("after", new)):
                values[name] = {
                    "first_u32le": int.from_bytes(data[:4], "little"),
                    "second_u32le": int.from_bytes(data[4:8], "little"),
                    "owner_id": data[8],
                }
    checks = {
        "packet_count": len(base.packets) == len(frame.packets) == expected["packet_count"],
        "frame_end_byte": base.end_byte == frame.end_byte == expected["frame_end_byte"],
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(frame.packets) == frame.encoded_body,
        "selector_order_unchanged": list(before) == list(after),
        "baseline_reference_bytes": all(
            b"".join(p.payload for p in before.get(key, ())).hex()
            == expected["reference_before_hex"][str(key)]
            for key in ids
        ),
        "reference_locations_unchanged": all(
            groups_before.get(key)
            == groups_after.get(key)
            == expected["reference_packet_indices"][str(key)]
            for key in ids
        ),
        "reference_sizes_and_owners": all(
            len(data := b"".join(p.payload for p in after.get(key, ())))
            == expected["reference_record_bytes"]
            and data[8] == expected["owner_id"]
            for key in ids
        ),
        "exactly_one_sound9_reference_changed": one,
        "only_one_reference_packet_changed": one and changed_packets == groups_after[changed[0]],
        "only_allowed_reference_bytes_changed": bool(changes)
        and all(c["offset"] in expected["only_allowed_payload_offsets"] for c in changes),
        "every_other_plain_packet_unchanged": one
        and tuple(p for i, p in enumerate(base.packets) if i not in groups_before[changed[0]])
        == tuple(p for i, p in enumerate(frame.packets) if i not in groups_after[changed[0]]),
        "other_sound_records_and_backing_codes_unchanged": all(
            before.get(key) == after.get(key)
            for key in before.keys() | after.keys()
            if key not in ids
        ),
        "all_patterns_unchanged": all(
            pattern_data(base, p) == pattern_data(frame, p) for p in range(1, 17)
        ),
    }
    return checks, changed_packets, changed, changes, values


def comparison_checks(base, frame, registration):
    checks, changed_packets, changed, changes, values = reference_comparison_checks(
        base, frame, registration
    )
    hypotheses = registration["separately_evaluated_hypotheses"]
    low, high = hypotheses["second_field_moves_lower"]["expected_range_exclusive"]
    fits = {
        "key1_maps_to_selector8": changed
        == hypotheses["key1_maps_to_selector8"]["expected_changed_selector_ids"],
        "first_field_unchanged_zero": values is not None
        and values["before"]["first_u32le"]
        == values["after"]["first_u32le"]
        == hypotheses["first_field_unchanged_zero"]["expected_value"],
        "second_field_is_zero_start_melodic_minimum": values is not None
        and values["after"]["second_u32le"]
        == hypotheses["second_field_is_zero_start_melodic_minimum"]["expected_value"],
        "second_field_moves_lower": values is not None
        and low < values["after"]["second_u32le"] < high,
    }
    return checks, fits, changed_packets, changed, changes, values


def main():
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments/drum9-key1-trim-min-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    directory = root / "experiments/event-016-b-drum9-key1-trim-min"
    source_path = directory / registration["baseline_artifact"]
    capture = directory / "capture.wav"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    output = root / "experiments/drum9-key1-trim-min-results-001.json"
    validate_outputs([output], [registration_path, source_path, capture, artifact_path], False)
    source, recorded = load_artifact(source_path), load_artifact(artifact_path)
    base, frame = decode_artifact(source), decode_artifact(recorded)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Baseline or capture differs from registered source identity")
    checks, fits, packets, selectors, changes, values = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "first-drum-slice-minimum-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "changed_plain_packet_indices": packets,
        "changed_selector_ids": selectors,
        "reference_byte_changes": changes,
        "reference_values": values,
        "native_frame": frame_report(frame),
        "user_report": "done",
        "drum_writer_enabled": False,
        "limits": [
            "Key1 maps to selector8 and start0 is retained; the exact melodic-minimum79 prediction fails",
            "Observed127 is not substituted into the original prediction or declared a general drum minimum",
            "The other15 drum references and all unrelated state remain intact; no generated drum edit has been tested",
            "Minimum quantization, endpoint inclusivity and other keyboard-key mappings remain unresolved",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Single drum-reference preservation failed; report retained")


if __name__ == "__main__":
    main()
