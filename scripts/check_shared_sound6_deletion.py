"""Observe deletion of owner Sound6 while Sound7 retains a copied reference."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import Packet, decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data, grouped_packets
from scripts.check_shared_owner_rerecord import payload, zero_start_window


def hypothetical_transfer_packets(base):
    """Prediction only: clear selector5 and move the full buffer to self-owner6."""
    groups = grouped_packets(base)
    old = payload(groups, 5)
    if len(old) != 32777 or old[:9].hex() != "00000000c078000005" or payload(groups, 6) != old[:9]:
        raise ValueError("Exact observed Sound6 owner and Sound7 reference required")
    replacement = old[:8] + b"\x06" + old[9:]
    chunks, offset = [], 0
    for packet in groups[5]:
        length = len(packet.payload)
        chunks.append(Packet(0xEF78, replacement[offset : offset + length]))
        offset += length
    if offset != len(replacement):
        raise ValueError("Owner packet lengths do not cover predicted transfer")
    packets, selector = [], None
    for packet in base.packets:
        if packet.tag == 0x68B5:
            selector = packet.payload[0]
            packets.append(packet)
            if selector == 6:
                packets.extend(chunks)
        elif packet.tag != 0xEF78 or selector not in (5, 6):
            packets.append(packet)
    return tuple(packets)


def comparison_checks(base, actual, registration):
    expected = registration["control_checks"]
    before, after = grouped_packets(base), grouped_packets(actual)
    old6, old7 = payload(before, 5), payload(before, 6)
    new6, new7 = payload(after, 5), payload(after, 6)
    before_window, before_view = zero_start_window(before, 6)
    after_window, after_view = zero_start_window(after, 6)
    referrers = [key for key in before if len(data := payload(before, key)) >= 9 and data[8] == 5]
    checks = {
        "baseline_packet_count": len(base.packets) == expected["baseline_packet_count"],
        "baseline_sound6_payload_header_and_capacity": hashlib.sha256(old6).hexdigest()
        == expected["baseline_sound6_payload_sha256"]
        and old6[:9].hex() == expected["baseline_sound6_header_hex"]
        and len(old6) - 9 == expected["baseline_sound6_code_count"],
        "baseline_sound7_exact_reference": old7.hex() == expected["baseline_sound7_reference_hex"],
        "baseline_owner5_referrers": referrers == expected["baseline_owner5_referrers"] == [5, 6],
        "baseline_sound7_window_resolved": before_view["resolved"],
        "baseline_pattern_identities": all(
            hashlib.sha256(pattern_data(base, n)).hexdigest()
            == expected["pattern_sha256_by_slot"][str(n)]
            for n in range(1, 17)
        ),
        "state_changed_from_baseline": actual.packets != base.packets,
        "selector_order_unchanged": list(before) == list(after) == expected["selector_ids"],
        "all_patterns_unchanged": all(
            pattern_data(base, n) == pattern_data(actual, n) for n in range(1, 17)
        ),
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
    }
    model = registration["full_transfer_model"]
    fits = {
        "sound6_record_is_empty": not new6,
        "sound7_is_self_owned_full_buffer_with_all_codes_preserved": len(new7) == len(old6)
        and new7[:8] == old6[:8]
        and new7[8:9] == b"\x06"
        and new7[9:] == old6[9:],
        "sound7_logical_window_preserved": before_window is not None
        and after_window is not None
        and before_window == after_window,
        "sound7_reference_still_points_to_old_owner5": new7 == old7,
        "full_codes_remain_under_sound6_owner5": len(new6) == len(old6)
        and new6[:4] == bytes(4)
        and new6[8:9] == b"\x05"
        and new6[9:] == old6[9:],
        "all_other_sound_records_unchanged": all(
            before.get(key) == after.get(key)
            for key in before.keys() | after.keys()
            if key not in (5, 6)
        ),
        "all_non_sound6_and7_plain_packets_unchanged": excluding_destination_data(base, [5, 6])
        == excluding_destination_data(actual, [5, 6]),
        "full_transfer_geometry_matches": len(actual.packets) == model["packet_count"]
        and actual.end_byte == model["frame_end_byte"]
        and len(actual.encoded_body) - len(base.encoded_body) == model["native_body_byte_delta"],
        "full_transfer_entire_body_matches": hashlib.sha256(actual.encoded_body).hexdigest()
        == model["body_sha256"],
    }
    changed = sorted(
        key for key in before.keys() | after.keys() if before.get(key) != after.get(key)
    )
    records = []
    for key in changed:
        record = {"selector_id": key}
        for label, groups in (("before", before), ("after", after)):
            data = payload(groups, key)
            info = {
                "payload_bytes": len(data),
                "packet_count": len(groups.get(key, ())),
                "payload_sha256": hashlib.sha256(data).hexdigest(),
            }
            if len(data) >= 9:
                info.update(
                    header_hex=data[:9].hex(),
                    first_u32le=int.from_bytes(data[:4], "little"),
                    second_u32le=int.from_bytes(data[4:8], "little"),
                    owner_id=data[8],
                    bytes_after_header=len(data) - 9,
                )
            record[label] = info
        records.append(record)
    observed = {
        "sound7_before_window": before_view,
        "sound7_after_window": after_view,
        "packet_count_delta": len(actual.packets) - len(base.packets),
        "native_body_byte_delta": len(actual.encoded_body) - len(base.encoded_body),
    }
    return checks, fits, changed, records, observed


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-026-b-delete-shared-sound6"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact", type=Path, default=directory / "derived/analysis-001/capture.symbols.npz"
    )
    args = parser.parse_args()
    registration_path = root / "experiments/shared-sound6-deletion-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    source_path, baseline_capture = (
        root / registration["baseline_artifact"],
        root / registration["baseline_capture"],
    )
    capture = directory / "capture.wav"
    output = root / "experiments/shared-sound6-deletion-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, baseline_capture, capture, args.artifact], False
    )
    source, recorded = load_artifact(source_path), load_artifact(args.artifact)
    base, actual = decode_artifact(source), decode_artifact(recorded)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(baseline_capture) != registration["baseline_source_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Baseline or deletion capture identity differs from registration")
    checks, fits, changed, records, observed = comparison_checks(base, actual, registration)
    report = {
        "analysis_version": "shared-sound6-deletion-control-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(args.artifact),
        "artifact_path": str(args.artifact),
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "changed_selector_ids": changed,
        "changed_sound_records": records,
        "observed_ownership": observed,
        "native_frame": frame_report(actual),
        "deletion_writer_enabled": False,
        "limits": registration["limits"],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Shared-owner deletion control failed; report retained")


if __name__ == "__main__":
    main()
