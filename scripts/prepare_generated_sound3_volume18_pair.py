"""Prepare a genuine uniform21 reference and fixed research18 probe for gain ordering."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report, rebuild_labels
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact

REFERENCE_BODY = "937b33f0c2be408e8f2321e3dabb146b2ae74976ed9ded6ddec3a3214cdd13e4"
DIRECTORIES = ("replayed-sound3-volume21-reference-001", "edited-sound3-volume18-001")


def candidate_packets(frame):
    """Research only: exact genuine uniform reference required, fixed target18 only."""
    if hashlib.sha256(frame.encoded_body).hexdigest() != REFERENCE_BODY:
        raise ValueError("Exact independently captured uniform21 source required")
    data = bytearray(pattern_data(frame, 1))
    for step in range(16):
        p = 48 * step + 6
        before = (data[p] >> 6) | ((data[p + 1] & 15) << 2)
        if before != 21:
            raise ValueError("All16 source candidate fields must equal21")
        data[p] = (data[p] & 0x3F) | (2 << 6)
        data[p + 1] = (data[p + 1] & 0xF0) | 4
    return _replace_pattern_data(frame, 1, bytes(data))


def main():
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in DIRECTORIES]
    registration_path = root / "experiments/sound3-generated-volume18-pair-registration-001.json"
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh pair registration and both output directories required")
    source_folder = root / "experiments/event-047-d-sound3-volume-lock-quarter"
    observation_path = source_folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or observation["contiguous_model_raw_values_by_step"] != [21] * 16
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(source_folder / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Verified genuine uniform21 reference required")
    source = load_artifact(source_path)
    base = decode_artifact(source)
    unchanged = source.to_bytes()
    legs = []
    for directory, value, packets in zip(
        directories, (21, 18), (base.packets, candidate_packets(base))
    ):
        edited = rebuild_labels(source, packets)
        edited.metadata["transformations"].append(
            {
                "kind": "research-volume-ordering-reference-or-probe",
                "contiguous_raw_code": value,
                "hardware_verified": False,
            }
        )
        target = decode_artifact(edited)
        before, after = pattern_data(base, 1), pattern_data(target, 1)
        masked_before, masked_after = bytearray(before), bytearray(after)
        for step in range(16):
            for masked in (masked_before, masked_after):
                masked[48 * step + 6] &= 0x3F
                masked[48 * step + 7] &= 0xF0
        checks = {
            "reference_body_exact_or_candidate_mask_only": target.encoded_body == base.encoded_body
            if value == 21
            else masked_before == masked_after,
            "all_non_pattern_packets_exact": tuple(p for p in base.packets if p.tag != 0xC498)
            == tuple(p for p in target.packets if p.tag != 0xC498),
            "other15_patterns_exact": all(
                pattern_data(base, slot) == pattern_data(target, slot) for slot in range(2, 17)
            ),
            "all16_contiguous_raw_fields_match_target": all(
                ((after[48 * step + 6] >> 6) | ((after[48 * step + 7] & 15) << 2)) == value
                for step in range(16)
            ),
            "native_geometry_exact": len(target.packets) == 815 and target.end_byte == 156758,
            "source_artifact_preserved": source.to_bytes() == unchanged,
        }
        if not all(checks.values()):
            raise ValueError("Volume pair preservation failed")
        waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
        directory.mkdir()
        write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
        write_bytes(directory / "restore.wav", waveform)
        recovered = decode_wav(directory / "restore.wav", 0.02)
        write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
        comparison = compare_artifacts(edited, recovered)
        decoded = decode_artifact(recovered)
        checks.update(
            strict_phase_roundtrip=comparison["passed"],
            entire_target_body_after_wav_decode=decoded.encoded_body == target.encoded_body,
            entire_target_packets_after_wav_decode=decoded.packets == target.packets,
            source_file_preserved=sha256_file(source_path) == observation["artifact_sha256"],
        )
        report = {
            "analysis_version": "volume21-reference-and-research18-software-validation-0.1",
            "hardware_verified": False,
            "passed": all(checks.values()),
            "checks": checks,
            "encoding": encoding,
            "strict_phase_roundtrip": comparison,
            "target_frame": frame_report(target),
            "restore_wav_sha256": sha256_file(directory / "restore.wav"),
            "edited_artifact_sha256": sha256_file(directory / "edited.symbols.npz"),
        }
        write_bytes(directory / "software-validation.json", json_bytes(report))
        if not report["passed"]:
            raise ValueError("Volume waveform pair failed software checks; outputs retained")
        legs.append(
            {
                "experiment_id": directory.name,
                "contiguous_raw_code": value,
                "alternative_order_raw_code": 21 if value == 21 else 36,
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "edited_artifact_sha256": report["edited_artifact_sha256"],
                "software_validation_sha256": sha256_file(directory / "software-validation.json"),
                "backup_file": "capture.wav",
                "ordinary_playback_file": "playback.wav",
            }
        )
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_uniform21_reference_restore_backup_and_audio"
                    if value == 21
                    else "awaiting_verified_reference_then_generated18_restore_backup_and_audio",
                    "restore_file": "restore.wav",
                    "registration": "../sound3-generated-volume18-pair-registration-001.json",
                    "hardware_restore": {"status": "not_run"},
                    "planned_actions": [
                        "For generated18 wait until reference native capture and ordinary playback are verified",
                        "Restore complete restore.wav with established stereo path and level; keep both knobs and recording/output levels unchanged",
                        "Select Pattern1/Sound3/TONE stopped/write off; before pattern playback save complete capture.wav with established reduced levels and one second tail",
                        "Separately record12 to15 seconds of ordinary Pattern1 playback as playback.wav,then stop/write off",
                        "Report restore success and same recognizable phrase; no numeric volume display inferred or read by moving B",
                    ],
                }
            ),
        )
    registration = {
        "analysis_version": "generated-volume21-versus18-gain-ordering-preregistration-0.1",
        "registered_before_all_captures": True,
        "hardware_verified": False,
        "source_artifact": source_path.relative_to(root).as_posix(),
        "source_artifact_sha256": observation["artifact_sha256"],
        "source_capture": (source_folder / "capture.wav").relative_to(root).as_posix(),
        "source_capture_sha256": observation["capture_sha256"],
        "source_body_sha256": REFERENCE_BODY,
        "source_observation_sha256": sha256_file(observation_path),
        "interior_results_sha256": sha256_file(
            root / "experiments/sound3-volume-middle-series-results-001.json"
        ),
        "expected_capture_sequence": legs,
        "gain_hypotheses": {
            "contiguous_order": "Reference21 versus generated18: Sound3 repeated-tone amplitude should decrease",
            "alternative_order": "Reference21 versus generated36: Sound3 repeated-tone amplitude should increase",
            "pitch_and_timing": "Repeated-tone frequency and onset intervals must remain unchanged; samples,keys and all other parameters remain exact",
            "minimum_relative_amplitude_difference": 0.03,
            "unchanged_pitch_relative_tolerance": 0.005,
            "unchanged_loop_seconds_tolerance": 0.005,
            "minimum_complete_cycles": 3,
            "nominal_loop_seconds": 2.4,
            "reference_tone_lead_hz": 500.65,
        },
        "limits": [
            "Reference21 is common to both encodings and exactly reproduces the independent genuine quarter body",
            "Generated18 is a fixed new research value; no public volume writer enabled",
            "Amplitude comparison needs unchanged audio settings and independent ordinary recordings; no linear,dB or percent gain curve assumed",
            "The failed uniform-middle and four-bit reports remain immutable; this is a separate generated ordering test",
            "First verify reference reception and usable audio before requesting candidate18 restoration",
            "Software never becomes hardware verification; missing evidence remains unevaluated",
        ],
    }
    write_bytes(registration_path, json_bytes(registration))
    print(
        json.dumps(
            {
                "passed": True,
                "legs": legs,
                "gain_ordering_discriminant": "18<21 for contiguous versus36>21 for alternative",
            }
        )
    )


if __name__ == "__main__":
    main()
