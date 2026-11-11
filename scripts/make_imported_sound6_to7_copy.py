"""Prepare an isolated reference-copy probe for the accepted mono WAV import."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    frame_report,
    rebuild_labels,
    sound_data,
    sound_groups,
)
from po33_re.formats.samples import sound_at_48k
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact
from scripts.check_sound6_to7_copy_restore import comparison_checks


def copy_imported_reference(frame):
    """Only the verified 32768-code chirp owner5 into existing empty Sound7."""
    groups = sound_groups(frame)
    if 6 not in groups or groups[6]:
        raise ValueError("Existing empty Sound7 required")
    data = sound_data(frame, 5)
    if (
        len(data) != 32777
        or data[:9].hex() != "00000000ab44000005"
        or hashlib.sha256(data).hexdigest()
        != "7fa1522cf7cf5bbb592ef71ff4e0934ff6b3878b62f5537405c5bb61f7843e40"
    ):
        raise ValueError("Exact hardware-verified imported chirp owner required")
    referrers = []
    for key, indices in groups.items():
        if not indices:
            continue
        record = sound_data(frame, key)
        if len(record) < 9 or record[8] == 6:
            raise ValueError("Malformed record or reference to empty Sound7")
        if record[8] == 5:
            referrers.append(key)
    if referrers != [5]:
        raise ValueError("Sound6 must be unshared")
    index = next(i for i, packet in enumerate(frame.packets) if packet == Packet(0x68B5, b"\x06"))
    return frame.packets[: index + 1] + (Packet(0xEF78, data[:9]),) + frame.packets[index + 1 :]


def run(directory):
    root = Path(__file__).resolve().parents[1]
    if directory.exists() or directory.is_symlink() or not directory.parent.is_dir():
        raise ValueError("Fresh output directory with an existing parent required")
    baseline = root / "experiments/edited-sound6-mono-WAV-import-001"
    acceptance_path = baseline / "hardware-acceptance-001.json"
    acceptance = json.loads(acceptance_path.read_text())
    source_path = root / acceptance["artifact_path"]
    if (
        not acceptance["hardware_verified"]
        or not all(acceptance["checks"].values())
        or sha256_file(source_path) != acceptance["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != acceptance["capture_sha256"]
    ):
        raise ValueError("Verified mono import source and unchanged files required")
    source = load_artifact(source_path)
    source_bytes = source.to_bytes()
    original = decode_artifact(source)
    if hashlib.sha256(original.encoded_body).hexdigest() != acceptance["body_sha256"]:
        raise ValueError("Verified mono import body differs")
    edited = rebuild_labels(source, copy_imported_reference(original))
    edited.metadata["transformations"].append(
        {
            "kind": "imported-Sound6-to-empty-Sound7-reference-copy-probe",
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    registration = {
        "analysis_version": "imported-Sound6-to7-copy-preregistration-0.1",
        "registered_before_capture": True,
        "source_artifact": source_path.relative_to(root).as_posix(),
        "source_artifact_sha256": acceptance["artifact_sha256"],
        "source_capture_sha256": acceptance["capture_sha256"],
        "source_acceptance_sha256": sha256_file(acceptance_path),
        "source_body_sha256": acceptance["body_sha256"],
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_packet_count": 952,
        "expected_frame_end_byte": 190229,
        "expected_sound7_reference_hex": "00000000ab44000005",
        "expected_sound6_payload_sha256": "7fa1522cf7cf5bbb592ef71ff4e0934ff6b3878b62f5537405c5bb61f7843e40",
        "limits": [
            "Only this unchanged imported Sound6 owner and empty Sound7 are tested",
            "One nine-byte reference is inserted; no backing codes or allocation are added",
            "Public copy/deletion guards are unchanged pending appropriate evidence",
        ],
    }
    checks = comparison_checks(original, target, target, registration)
    stale_checks = comparison_checks(original, target, original, registration)
    left, _ = sound_at_48k(target, 6)
    right, _ = sound_at_48k(target, 7)
    checks.update(
        previews_identical=np.array_equal(left, right),
        stale_source_rejected=not all(stale_checks.values()),
        one_reference_packet_only=len(target.packets) == len(original.packets) + 1
        and len(target.encoded_body) == len(original.encoded_body) + 14,
        source_artifact_preserved=source.to_bytes() == source_bytes,
    )
    if not all(checks.values()):
        raise ValueError("Imported reference-copy locality or geometry checks failed")
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    directory.mkdir()
    write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
    write_bytes(directory / "restore.wav", waveform)
    recovered = decode_wav(directory / "restore.wav", 0.02)
    write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
    decoded = decode_artifact(recovered)
    roundtrip = compare_artifacts(edited, recovered)
    checks.update(
        strict_phase_roundtrip=roundtrip["passed"],
        entire_target_body_after_wav_decode=decoded.encoded_body == target.encoded_body,
        source_file_preserved=sha256_file(source_path) == acceptance["artifact_sha256"],
    )
    report = dict(registration)
    report.update(
        analysis_version="imported-Sound6-to7-copy-software-validation-0.1",
        checks=checks,
        passed=all(checks.values()),
        hardware_verified=False,
        encoding=encoding,
        strict_phase_roundtrip=roundtrip,
        target_frame=frame_report(target),
        restore_wav_sha256=sha256_file(directory / "restore.wav"),
        edited_artifact_sha256=sha256_file(directory / "edited.symbols.npz"),
    )
    write_bytes(directory / "software-validation.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Waveform checks failed; outputs retained")
    registration.update(
        restore_wav_sha256=report["restore_wav_sha256"],
        edited_artifact_sha256=report["edited_artifact_sha256"],
        software_validation_sha256=sha256_file(directory / "software-validation.json"),
        expected_auditions={
            "sound6_and_sound7_key1": "Matching rising pitch sweeps about 0.75 seconds",
            "other_sounds_and_pattern1": "Unchanged",
        },
    )
    write_bytes(directory / "restore-registration.json", json_bytes(registration))
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": directory.name,
                "capture_status": "awaiting_imported_reference_copy_restore",
                "expected_file": "capture.wav",
                "restore_file": "restore.wav",
                "registration": "restore-registration.json",
                "hardware_restore": {"status": "not_run", "observations": []},
                "planned_actions": [
                    "Restore complete restore.wav at the established stereo playback level",
                    "Select Pattern1/Sound8/TONE stopped/write off, keeping both knobs unchanged",
                    "Before audition save complete stereo capture.wav at the established reduced levels with one second trailing silence",
                    "After saving compare Sound6/key1 and Sound7/key1 sweeps, confirm other sounds and Pattern1 unchanged; return to Sound8/TONE",
                ],
            }
        ),
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.out_dir)
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "expected_body_sha256": report["expected_body_sha256"],
                "restore_wav_sha256": report["restore_wav_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
