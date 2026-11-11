"""Register a physical Sound6 deletion control for the copied imported chirp."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
)
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import grouped_packets
from scripts.check_shared_owner_rerecord import payload
from scripts.check_shared_sound6_deletion import comparison_checks

FULL_TRANSFER_CHECKS = (
    "sound6_record_is_empty",
    "sound7_is_self_owned_full_buffer_with_all_codes_preserved",
    "sound7_logical_window_preserved",
    "all_other_sound_records_unchanged",
    "all_non_sound6_and7_plain_packets_unchanged",
    "full_transfer_geometry_matches",
    "full_transfer_entire_body_matches",
)


def predict_imported_transfer(base):
    """Prediction only for this exact imported owner and single matching reference."""
    groups = grouped_packets(base)
    old = payload(groups, 5)
    if (
        len(old) != 32777
        or old[:9].hex() != "00000000ab44000005"
        or hashlib.sha256(old).hexdigest()
        != "7fa1522cf7cf5bbb592ef71ff4e0934ff6b3878b62f5537405c5bb61f7843e40"
        or payload(groups, 6) != old[:9]
        or [key for key in groups if len(data := payload(groups, key)) >= 9 and data[8] == 5]
        != [5, 6]
    ):
        raise ValueError("Exact imported Sound6 owner and single Sound7 reference required")
    for number in range(1, 17):
        raw = pattern_data(base, number)
        for step in range(16):
            for sound in (5, 6):
                offset = 48 * step + 3 * sound
                if raw[offset : offset + 3] != bytes(3) or raw[768 + 16 * step + sound]:
                    raise ValueError("Deletion with Sound6/Sound7 pattern events is unverified")
    chunks = list(groups[5])
    first = chunks[0]
    chunks[0] = Packet(first.tag, first.payload[:8] + b"\x06" + first.payload[9:])
    output, selector = [], None
    for packet in base.packets:
        if packet.tag == 0x68B5:
            selector = packet.payload[0]
            output.append(packet)
            if selector == 6:
                output.extend(chunks)
        elif packet.tag != 0xEF78 or selector not in (5, 6):
            output.append(packet)
    return tuple(output)


def run(directory):
    root = Path(__file__).resolve().parents[1]
    if directory.exists() or directory.is_symlink() or not directory.parent.is_dir():
        raise ValueError("Fresh output directory with an existing parent required")
    baseline = root / "experiments/edited-imported-sound6-to7-copy-001"
    acceptance_path = baseline / "hardware-acceptance-001.json"
    acceptance = json.loads(acceptance_path.read_text())
    source_path = root / acceptance["artifact_path"]
    if (
        not acceptance["hardware_verified"]
        or not all(acceptance["checks"].values())
        or sha256_file(source_path) != acceptance["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != acceptance["capture_sha256"]
    ):
        raise ValueError("Verified imported-copy source required")
    base = decode_artifact(load_artifact(source_path))
    if hashlib.sha256(base.encoded_body).hexdigest() != acceptance["body_sha256"]:
        raise ValueError("Verified source body differs")
    target = decode_frame(bytes(4095) + encode_packets(predict_imported_transfer(base)))
    groups = grouped_packets(base)
    old = payload(groups, 5)
    registration = {
        "analysis_version": "physical-imported-shared-Sound6-deletion-preregistration-0.1",
        "registered_before_capture": True,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": acceptance["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_source_sha256": acceptance["capture_sha256"],
        "baseline_body_sha256": acceptance["body_sha256"],
        "baseline_acceptance_sha256": sha256_file(acceptance_path),
        "control_checks": {
            "baseline_packet_count": 952,
            "baseline_sound6_payload_sha256": hashlib.sha256(old).hexdigest(),
            "baseline_sound6_header_hex": old[:9].hex(),
            "baseline_sound6_code_count": 32768,
            "baseline_sound7_reference_hex": old[:9].hex(),
            "baseline_owner5_referrers": [5, 6],
            "pattern_sha256_by_slot": {
                str(n): hashlib.sha256(pattern_data(base, n)).hexdigest() for n in range(1, 17)
            },
            "selector_ids": list(groups),
        },
        "full_transfer_model": {
            "packet_count": 951,
            "frame_end_byte": 190215,
            "native_body_byte_delta": -14,
            "body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
            "sound7_header_hex": "00000000ab44000006",
        },
        "limits": [
            "This is a preregistered prediction of physical deletion, not a new hardware result",
            "No generated restore is needed; delete only Sound6 in the current verified copied state",
            "Public deletion guards remain unchanged until this imported endpoint is observed",
        ],
    }
    controls, fits, changed, _, _ = comparison_checks(base, target, registration)
    stale_controls, stale_fits, _, _, _ = comparison_checks(base, base, registration)
    checks = {
        "all_target_core_controls": all(controls.values()),
        "all_full_transfer_hypotheses": all(fits[name] for name in FULL_TRANSFER_CHECKS),
        "only_sound6_and7_change": changed == [5, 6],
        "retained_owner_and_reference_alternatives_fail": not fits[
            "sound7_reference_still_points_to_old_owner5"
        ]
        and not fits["full_codes_remain_under_sound6_owner5"],
        "stale_baseline_rejected": not all(stale_controls.values())
        and not stale_fits["full_transfer_entire_body_matches"],
    }
    assert all(checks.values()), checks
    directory.mkdir()
    write_bytes(directory / "predicted-native-body.bin", target.encoded_body)
    registration["predicted_body_file_sha256"] = sha256_file(
        directory / "predicted-native-body.bin"
    )
    write_bytes(directory / "deletion-registration.json", json_bytes(registration))
    write_bytes(
        directory / "software-prediction-validation.json",
        json_bytes(
            {
                "analysis_version": "imported-shared-deletion-prediction-check-0.1",
                "hardware_verified": False,
                "passed": True,
                "checks": checks,
                "registration_sha256": sha256_file(directory / "deletion-registration.json"),
            }
        ),
    )
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": directory.name,
                "capture_status": "awaiting_physical_imported_shared_sound6_deletion",
                "baseline_id": baseline.name,
                "expected_file": "capture.wav",
                "registration": "deletion-registration.json",
                "planned_actions": [
                    "Select Sound6 and release both buttons; hold record and press sound to delete selected Sound6 only",
                    "Return to Pattern1/Sound8/TONE stopped/write off, both knobs unchanged",
                    "Before audition record complete stereo capture.wav with one second trailing silence at established reduced levels",
                    "Then confirm Sound6 silent, Sound7 same rising sweep, Sound4/Sound5/Pattern1 unchanged; return to Sound8/TONE",
                ],
            }
        ),
    )
    return registration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out_dir)
    print(
        json.dumps(
            {
                "registered": True,
                "predicted_body_sha256": result["full_transfer_model"]["body_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
