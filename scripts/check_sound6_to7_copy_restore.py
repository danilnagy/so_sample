"""Check a generated Sound6-to7 reference-copy recapture against its target."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import (
    decode_artifact,
    encode_packets,
    frame_report,
    sound_data,
    sound_groups,
)
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data


def comparison_checks(base, target, actual, registration):
    groups = sound_groups(actual)
    reference = b"".join(actual.packets[i].payload for i in groups.get(6, []))
    referrers = [
        key
        for key, indices in groups.items()
        if indices and len(data := sound_data(actual, key)) >= 9 and data[8] == 5
    ]
    return {
        "source_body_matches": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "source_destination_empty": sound_groups(base)[6] == [],
        "registered_target_body_matches": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_recaptured_native_body_matches_target": actual.encoded_body == target.encoded_body,
        "entire_recaptured_plain_packets_match_target": actual.packets == target.packets,
        "expected_reference_copy_geometry": len(actual.packets)
        == registration["expected_packet_count"]
        and actual.end_byte == registration["expected_frame_end_byte"],
        "sound7_exact_reference": reference.hex() == registration["expected_sound7_reference_hex"]
        and len(reference) == 9,
        "sound6_full_buffer_preserved": sound_data(actual, 5) == sound_data(base, 5)
        and hashlib.sha256(sound_data(actual, 5)).hexdigest()
        == registration["expected_sound6_payload_sha256"],
        "owner5_has_only_sound6_and7_referrers": referrers == [5, 6],
        "all_patterns_preserved": all(
            pattern_data(base, n) == pattern_data(actual, n) for n in range(1, 17)
        ),
        "all_non_sound7_plain_packets_preserved": excluding_destination_data(base, [6])
        == excluding_destination_data(actual, [6]),
        "all_native_checksums": True,
        "exact_body_reencode": encode_packets(actual.packets) == actual.encoded_body,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument(
        "--experiment-dir", type=Path, default=root / "experiments/edited-sound6-to7-copy-001"
    )
    args = parser.parse_args()
    directory = args.experiment_dir
    artifact_path = args.artifact or directory / "derived/analysis-001/capture.symbols.npz"
    registration_path = directory / "restore-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["source_artifact"]
    target_path, capture_path = directory / "edited.symbols.npz", directory / "capture.wav"
    report_path = directory / "hardware-recapture-results-001.json"
    validate_outputs(
        [report_path],
        [registration_path, source_path, target_path, capture_path, artifact_path],
        False,
    )
    recorded = load_artifact(artifact_path)
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(target_path) != registration["edited_artifact_sha256"]
        or sha256_file(directory / "restore.wav") != registration["restore_wav_sha256"]
        or sha256_file(directory / "software-validation.json")
        != registration["software_validation_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture_path)
    ):
        raise ValueError("Registered source, generated copy or recapture identity differs")
    base, target, actual = (
        decode_artifact(load_artifact(source_path)),
        decode_artifact(load_artifact(target_path)),
        decode_artifact(recorded),
    )
    checks = comparison_checks(base, target, actual, registration)
    report = {
        "analysis_version": "first-generated-sound6-to7-reference-copy-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture_path),
        "artifact_sha256": sha256_file(artifact_path),
        "artifact_path": str(artifact_path),
        "checks": checks,
        "passed": all(checks.values()),
        "native_frame": frame_report(actual),
        "audition_result": "Requires separate user observation; not inferred from packet checks",
        "limits": registration["limits"],
    }
    write_bytes(report_path, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Sound6-to7 reference-copy recapture differs; report retained")


if __name__ == "__main__":
    main()
