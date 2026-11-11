"""Report the first swing control, preserving failed location and direct-display hypotheses."""

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


def comparison_checks(base, actual, registration, display_value=None, display_text=None):
    if display_value is not None and (
        type(display_value) is not int or not 0 <= display_value <= 999
    ):
        raise ValueError(
            "Swing display value must be an independently observed integer from0 to999"
        )
    if display_text is not None and not isinstance(display_text, str):
        raise ValueError("Swing display text must be independently reported text")
    before, after = grouped_packets(base), grouped_packets(actual)
    old_globals, new_globals = [
        [p.payload for p in f.packets if p.tag == 0x7D5C] for f in (base, actual)
    ]
    candidate = registration["candidate"]
    occurrence, offset = (
        candidate["occurrence_index_zero_based"],
        candidate["payload_offset_zero_based"],
    )
    old = old_globals[occurrence] if len(old_globals) > occurrence else b""
    new = new_globals[occurrence] if len(new_globals) > occurrence else b""
    controls = {
        "baseline_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["baseline_body_sha256"],
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
        "selector_order_unchanged": list(before) == list(after),
        "all_sample_records_unchanged": before == after,
        "all_patterns_unchanged": all(
            pattern_data(base, n) == pattern_data(actual, n) for n in range(1, 17)
        ),
        "tempo137_preserved": len(old) > 129
        and len(new) > 129
        and old[129] == new[129] == registration["expected_tempo_bpm"],
    }
    changed = [i for i, (a, b) in enumerate(zip_longest(old, new)) if a != b]
    hypotheses = {
        "native_body_changed": actual.encoded_body != base.encoded_body,
        "same_packet_tags_and_lengths": [(p.tag, len(p.payload)) for p in base.packets]
        == [(p.tag, len(p.payload)) for p in actual.packets],
        "all_non_global_packets_unchanged": tuple(p for p in base.packets if p.tag != 0x7D5C)
        == tuple(p for p in actual.packets if p.tag != 0x7D5C),
        "two_global_records_keep_observed_sizes": len(old_globals) == len(new_globals) == 2
        and all(len(raw) == 255 for raw in old_globals + new_globals),
        "first_global_record_unchanged": bool(old_globals and new_globals)
        and old_globals[0] == new_globals[0],
        "only_registered_swing_candidate_byte_changed": changed == [offset],
        "candidate_equals_independently_reported_display_value": new[offset] == display_value
        if display_value is not None and len(new) > offset
        else None,
    }
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
                changed_payload_bytes=[
                    {"offset_zero_based": i, "before": a, "after": b}
                    for i, (a, b) in enumerate(zip_longest(left.payload, right.payload))
                    if a != b
                ],
                before_payload_bytes=len(left.payload),
                after_payload_bytes=len(right.payload),
            )
        differences.append(item)
    observed = {
        "display_value": display_value,
        "display_text": display_text,
        "candidate_before": old[offset] if len(old) > offset else None,
        "candidate_after": new[offset] if len(new) > offset else None,
        "candidate_changed_offsets": changed,
        "changed_packets": differences,
        "numeric_swing_encoding_confirmed": False,
    }
    return controls, hypotheses, observed


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-037-b-swing-maximum"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact", type=Path, default=directory / "derived/analysis-001/capture.symbols.npz"
    )
    parser.add_argument("--display-value", type=int)
    parser.add_argument("--display-text")
    args = parser.parse_args()
    registration_path = directory / "swing-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["baseline_artifact"]
    capture = directory / "capture.wav"
    output = directory / "native-swing-results-001.json"
    validate_outputs([output], [registration_path, source_path, capture, args.artifact], False)
    recorded = load_artifact(args.artifact)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(root / registration["baseline_capture"])
        != registration["baseline_capture_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Registered swing source or capture identities differ")
    base, actual = decode_artifact(load_artifact(source_path)), decode_artifact(recorded)
    controls, fits, observed = comparison_checks(
        base, actual, registration, args.display_value, args.display_text
    )
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "first-swing-maximum-control-check-0.1",
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": sha256_file(capture),
                "artifact_sha256": sha256_file(args.artifact),
                "control_checks": controls,
                "control_passed": all(controls.values()),
                "hypothesis_checks": fits,
                "observed_change": observed,
                "native_frame": frame_report(actual),
                "swing_writer_enabled": False,
                "limits": registration["limits"],
            }
        ),
    )
    if not all(controls.values()):
        raise ValueError("Swing control changed tempo or another core invariant; report retained")


if __name__ == "__main__":
    main()
