"""Check exact joint tempo100/swing9 recapture and an independent BPM reading."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.globals import calibrated_swing, calibrated_tempo
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact


def restore_checks(base, target, actual, registration, displayed_bpm=None):
    before, after = base.packets[2].payload, actual.packets[2].payload
    return {
        "source_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "supplied_target_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_recapture_body_matches_target": actual.encoded_body == target.encoded_body,
        "entire_recapture_packets_match_target": actual.packets == target.packets,
        "all_other_packets_exact": base.packets[:2] == actual.packets[:2]
        and base.packets[3:] == actual.packets[3:],
        "other_second_global_bytes_exact": before[:129] == after[:129]
        and before[131:] == after[131:],
        "tempo100_and_swing9_encoded": after[129:131] == bytes([100, 9]),
        "expected_native_geometry": len(actual.packets) == registration["expected_packet_count"]
        and actual.end_byte == registration["expected_frame_end_byte"],
        "independent_displayed_BPM_matches100": displayed_bpm == 100
        if displayed_bpm is not None
        else None,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-joint-tempo100-swing9-001"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact", type=Path, default=directory / "derived/analysis-001/capture.symbols.npz"
    )
    parser.add_argument("--displayed-bpm", type=int)
    args = parser.parse_args()
    registration_path = directory / "joint-global-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["source_artifact"]
    target_path = directory / "edited.symbols.npz"
    capture = directory / "capture.wav"
    output = directory / "hardware-recapture-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, target_path, capture, args.artifact], False
    )
    recorded = load_artifact(args.artifact)
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
        or sha256_file(target_path) != registration["edited_artifact_sha256"]
        or sha256_file(directory / "restore.wav") != registration["restore_wav_sha256"]
        or sha256_file(directory / "compile-report.json") != registration["compile_report_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Registered joint-edit source, target or recapture fingerprint differs")
    base, target, actual = [
        decode_artifact(item)
        for item in (load_artifact(source_path), load_artifact(target_path), recorded)
    ]
    checks = restore_checks(base, target, actual, registration, args.displayed_bpm)
    native_passed = all(
        value is True
        for key, value in checks.items()
        if key != "independent_displayed_BPM_matches100"
    )
    report = {
        "analysis_version": "joint-tempo100-swing9-recapture-check-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "checks": checks,
        "native_passed": native_passed,
        "joint_hypotheses_supported": all(value is True for value in checks.values()),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(args.artifact),
        "artifact_path": args.artifact.relative_to(root).as_posix(),
        "displayed_bpm": args.displayed_bpm,
        "native_frame": frame_report(actual),
        "limits": registration["limits"],
    }
    if native_passed:
        report["calibrated_readback"] = {
            "tempo_bpm": calibrated_tempo(actual),
            "swing_byte": calibrated_swing(actual),
        }
    write_bytes(output, json_bytes(report))
    if not native_passed:
        raise ValueError("Joint restore differs from registered native target; report retained")


if __name__ == "__main__":
    main()
