"""Prepare fixed16/52 FILTER research restores matching independent physical bodies."""

import argparse
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
from scripts.check_sound3_filter_probe import recorded_report
from scripts.check_sound3_filter_range import mask_preserved

CENTER_BODY = "8f80a398ac7130f1802ba865985cb3f7174f9f0129af1182eb6d5da450d6a341"
DIRECTORIES = ("edited-sound3-filter16-lowpass-001", "edited-sound3-filter52-highpass-001")
REGISTRATION = "sound3-generated-filter16-52-registration-001.json"


def fixed_packets(frame, value):
    if hashlib.sha256(frame.encoded_body).hexdigest() != CENTER_BODY:
        raise ValueError("Exact genuine uniform63 center required")
    if type(value) is not int or value not in (16, 52):
        raise ValueError("Only fixed research filter values16 and52 allowed")
    data = bytearray(pattern_data(frame, 1))
    for step in range(16):
        p = 48 * step + 6
        data[p + 1] = (data[p + 1] & 15) | ((value & 15) << 4)
        data[p + 2] = (data[p + 2] & 252) | (value >> 4)
    return _replace_pattern_data(frame, 1, bytes(data))


def preservation_checks(base, actual, value, registration):
    report = recorded_report(base, actual, registration)
    fields = report["raw_Sound3_fields"]["after"]
    return dict(
        report["native_checks"],
        **report["preservation_checks"],
        source_body_is_fixed_center=hashlib.sha256(base.encoded_body).hexdigest() == CENTER_BODY,
        only_strict_candidate_mask_changed=mask_preserved(base, actual),
        all16_candidate_values_equal_fixed_value=fields["uninterpreted_candidate_values"]
        == [value] * 16,
        pitch14_and_volume36_preserved=fields["first_low5_values"] == [14] * 16
        and fields["volume_values"] == [36] * 16,
    )


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in DIRECTORIES]
    registration_path = root / "experiments" / REGISTRATION
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh generated FILTER registration and directories required")
    folder = root / "experiments/event-061-h-return-sound3-filter-A-center"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    context = json.loads(
        (root / "experiments/sound3-filter-A-interior-registration-001.json").read_text()
    )
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Verified exact center return required")
    source = load_artifact(source_path)
    base = decode_artifact(source)
    unchanged = source.to_bytes()
    legs = []
    physical_ids = (
        "event-059-f-sound3-filter-A-lowpass-interior",
        "event-060-g-sound3-filter-A-highpass-interior",
    )
    for directory, value, physical_id in zip(directories, (16, 52), physical_ids):
        physical_folder = root / "experiments" / physical_id
        physical_observation_path = physical_folder / "hardware-observation-001.json"
        physical = json.loads(physical_observation_path.read_text())
        physical_path = root / physical["artifact_path"]
        if (
            not physical["hardware_verified"]
            or not all(physical["checks"].values())
            or physical["contiguous_candidate_values"] != [value] * 16
            or sha256_file(physical_path) != physical["artifact_sha256"]
            or sha256_file(physical_folder / "capture.wav") != physical["capture_sha256"]
        ):
            raise ValueError("Independent physically observed FILTER target required")
        independent = decode_artifact(load_artifact(physical_path))
        edited = rebuild_labels(source, fixed_packets(base, value))
        edited.metadata["transformations"].append(
            {"kind": "research-fixed-Sound3-filter", "raw_value": value, "hardware_verified": False}
        )
        target = decode_artifact(edited)
        checks = preservation_checks(base, target, value, context)
        checks["entire_target_matches_independent_physical_body_and_packets"] = (
            target.encoded_body == independent.encoded_body
            and target.packets == independent.packets
        )
        if not all(checks.values()):
            raise ValueError("FILTER target differs from independent body or strict scope")
        waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
        directory.mkdir()
        write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
        write_bytes(directory / "restore.wav", waveform)
        recovered = decode_wav(directory / "restore.wav", 0.02)
        write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
        comparison = compare_artifacts(edited, recovered)
        actual = decode_artifact(recovered)
        checks.update(
            strict_phase_roundtrip=comparison["passed"],
            entire_body_and_packets_after_wav_decode=actual.encoded_body == target.encoded_body
            and actual.packets == target.packets,
            source_memory_and_file_preserved=source.to_bytes() == unchanged
            and sha256_file(source_path) == observation["artifact_sha256"],
        )
        report = {
            "analysis_version": "fixed-filter16-52-native-and-waveform-validation-0.1",
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
            raise ValueError("Generated FILTER waveform failed; outputs retained")
        legs.append(
            {
                "experiment_id": directory.name,
                "raw_filter_value": value,
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "expected_audible_filter": "low_pass" if value == 16 else "high_pass",
                "restore_wav_sha256": report["restore_wav_sha256"],
                "edited_artifact_sha256": report["edited_artifact_sha256"],
                "software_validation_sha256": sha256_file(directory / "software-validation.json"),
                "independent_physical_artifact": physical["artifact_path"],
                "independent_physical_artifact_sha256": physical["artifact_sha256"],
                "independent_physical_observation": physical_observation_path.relative_to(
                    root
                ).as_posix(),
                "independent_physical_observation_sha256": sha256_file(physical_observation_path),
            }
        )
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_generated_lowpass_restore_backup_and_listening"
                    if value == 16
                    else "awaiting_verified_lowpass_then_generated_highpass_restore",
                    "restore_file": "restore.wav",
                    "registration": "../" + REGISTRATION,
                    "hardware_restore": {"status": "not_run"},
                    "planned_actions": [
                        "For52 wait until16 native reception and listening are verified",
                        "Restore through established stereo path and playback level; keep both knobs and recording settings unchanged",
                        "Before ordinary playback save full capture.wav here at reduced level with one second trailing silence",
                        "Select Pattern1/Sound3/FILTER with no knob movement; play and report successful restore plus actual filter sound, then stop/write off",
                        "No separate playback.wav or WRITE-held pass required",
                    ],
                }
            ),
        )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "generated-filter16-52-exact-target-and-listening-preregistration-0.1",
                "hardware_verified": False,
                "registered_before_both_generated_recaptures": True,
                "independent_physical_target_data_already_observed": True,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": CENTER_BODY,
                "source_observation_sha256": sha256_file(observation_path),
                "expected_packet_count": 815,
                "expected_frame_end_byte": 156758,
                "candidate": context["candidate"],
                "broader_FILTER_candidate": context["broader_FILTER_candidate"],
                "expected_capture_sequence": legs,
                "limits": [
                    "Targets reproduce known physical bodies; this new test concerns generated reception and saved-pattern audible behavior",
                    "Both generated targets and their hashes are frozen before recapture; no new general cutoff law or amplitude measurement is predicted",
                    "Restore16 and verify native plus user listening before requesting52; retain mismatches without changing targets",
                    "Only fixed16/52 from exact center are allowed by research constructor; public pitch/volume guards stay unchanged",
                    "Contiguous branch ordering has support but full field width, all-code law, numeric UI and resonance remain unknown",
                ],
            }
        ),
    )
    print(json.dumps({"passed": True, "hardware_verified": False, "legs": legs}))


if __name__ == "__main__":
    main()
