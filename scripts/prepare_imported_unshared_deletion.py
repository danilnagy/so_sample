"""Register physical removal of the last imported owner against an earlier genuine state."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data, grouped_packets
from scripts.check_shared_owner_rerecord import payload
from scripts.check_unshared_sound7_deletion import comparison_checks

REMOVAL_CHECKS = (
    "sound7_record_is_empty",
    "sound6_remains_empty",
    "all_other_sound_records_unchanged",
    "all_non_sound7_plain_packets_unchanged",
    "empty_record_geometry_matches",
    "entire_empty_record_model_matches",
)


def run(directory):
    root = Path(__file__).resolve().parents[1]
    if directory.exists() or directory.is_symlink() or not directory.parent.is_dir():
        raise ValueError("Fresh output directory with an existing parent required")
    baseline = root / "experiments/event-028-b-delete-imported-shared-sound6"
    acceptance_path = baseline / "hardware-acceptance-001.json"
    acceptance = json.loads(acceptance_path.read_text())
    source_path = root / acceptance["artifact_path"]
    if (
        not acceptance["hardware_verified"]
        or not all(acceptance["checks"].values())
        or sha256_file(source_path) != acceptance["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != acceptance["capture_sha256"]
    ):
        raise ValueError("Verified transferred imported owner required")
    source = decode_artifact(load_artifact(source_path))
    if hashlib.sha256(source.encoded_body).hexdigest() != acceptance["body_sha256"]:
        raise ValueError("Verified source body differs")
    groups = grouped_packets(source)
    old = payload(groups, 6)
    if len(old) != 32777 or old[:9].hex() != "00000000ab44000006" or payload(groups, 5):
        raise ValueError("Exact unshared imported Sound7 layout with empty Sound6 required")
    target = decode_frame(bytes(4095) + encode_packets(excluding_destination_data(source, [6])))
    earlier_path = (
        root
        / "experiments/event-027-b-delete-unshared-sound7/derived/analysis-001/capture.symbols.npz"
    )
    earlier_result_path = root / "experiments/unshared-sound7-deletion-results-001.json"
    earlier_result = json.loads(earlier_result_path.read_text())
    earlier = decode_artifact(load_artifact(earlier_path))
    if (
        sha256_file(earlier_path) != earlier_result["artifact_sha256"]
        or not earlier_result["control_passed"]
        or not earlier_result["hypothesis_checks"]["entire_empty_record_model_matches"]
        or earlier.encoded_body != target.encoded_body
    ):
        raise ValueError(
            "Predicted removal must recover the independently verified earlier native body"
        )
    registration = {
        "analysis_version": "physical-imported-last-owner-deletion-preregistration-0.1",
        "registered_before_capture": True,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": acceptance["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_source_sha256": acceptance["capture_sha256"],
        "baseline_body_sha256": acceptance["body_sha256"],
        "baseline_acceptance_sha256": sha256_file(acceptance_path),
        "control_checks": {
            "baseline_sound7_header_hex": old[:9].hex(),
            "baseline_sound7_payload_sha256": hashlib.sha256(old).hexdigest(),
            "baseline_owner6_referrers": [6],
            "pattern_sha256_by_slot": {
                str(n): hashlib.sha256(pattern_data(source, n)).hexdigest() for n in range(1, 17)
            },
            "selector_ids": list(groups),
        },
        "empty_record_model": {
            "body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
            "independently_observed_matching_state_artifact": earlier_path.relative_to(
                root
            ).as_posix(),
            "independent_artifact_sha256": sha256_file(earlier_path),
            "independent_results_sha256": sha256_file(earlier_result_path),
            "packet_count": 815,
            "frame_end_byte": 156758,
        },
        "limits": [
            "Only physical removal of this unshared Sound7 at endpoint17579 is tested",
            "Serialized record removal does not measure physical RAM reclamation",
            "Public Sound7 deletion retains its earlier endpoint guard pending this capture",
        ],
    }
    controls, fits, observed = comparison_checks(source, target, registration)
    stale_controls, stale_fits, _ = comparison_checks(source, source, registration)
    checks = {
        "all_target_core_controls": all(controls.values()),
        "all_removal_hypotheses": all(fits[name] for name in REMOVAL_CHECKS),
        "retained_full_owner_alternative_fails": not fits["full_codes_retained_under_owner6"],
        "only_sound7_changes": observed["changed_selector_ids"] == [6],
        "stale_source_rejected": not all(stale_controls.values())
        and not stale_fits["entire_empty_record_model_matches"],
        "whole_model_equals_earlier_independent_state": target.encoded_body == earlier.encoded_body,
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
                "analysis_version": "imported-last-owner-removal-prediction-check-0.1",
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
                "capture_status": "awaiting_physical_imported_unshared_sound7_deletion",
                "baseline_id": baseline.name,
                "expected_file": "capture.wav",
                "registration": "deletion-registration.json",
                "planned_actions": [
                    "Select Sound7 and release both buttons; hold record and press sound to delete selected Sound7 only",
                    "Return to Pattern1/Sound8/TONE stopped/write off, both knobs unchanged",
                    "Before audition record complete stereo capture.wav at the established reduced levels with one second trailing silence",
                    "Then confirm Sound6 and Sound7 silent, Sound4/Sound5/Pattern1 unchanged; return to Sound8/TONE",
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
                "predicted_body_sha256": result["empty_record_model"]["body_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
