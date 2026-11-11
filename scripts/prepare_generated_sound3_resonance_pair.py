"""Prepare fixed LPF16 with B0/B63 and preregister a common tone comparison."""

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

MINIMUM_BODY = "bee177abf44962fde6bee1279572df70c7f0b5cf87ffadc51ffaae4768d3d274"
DIRECTORIES = (
    "edited-sound3-filter16-B0-reference-001",
    "edited-sound3-filter16-B63-candidate-001",
)
REGISTRATION = "sound3-generated-filter16-B0-B63-registration-001.json"


def fixed_packets(frame, value):
    if hashlib.sha256(frame.encoded_body).hexdigest() != MINIMUM_BODY:
        raise ValueError("Exact genuine B0 minimum return required")
    if type(value) is not int or value not in (0, 63):
        raise ValueError("Only fixed research B0 and B63 are allowed")
    data = bytearray(pattern_data(frame, 1))
    for step in range(16):
        data[48 * step + 7] &= 15
        data[48 * step + 8] = 1 | (value << 2)
    return _replace_pattern_data(frame, 1, bytes(data))


def preservation_checks(base, actual, value, registration):
    report = recorded_report(base, actual, registration)
    before, after = [bytearray(pattern_data(frame, 1)) for frame in (base, actual)]
    for data in (before, after):
        for step in range(16):
            data[48 * step + 7] &= 15
            data[48 * step + 8] = 0
    fields = report["raw_Sound3_fields"]["after"]
    data = pattern_data(actual, 1)
    return dict(
        report["native_checks"],
        **report["preservation_checks"],
        source_is_exact_minimum=hashlib.sha256(base.encoded_body).hexdigest() == MINIMUM_BODY,
        only_FILTER_A_and_B_masks_changed=before == after,
        pitch14_and_volume36_preserved=fields["first_low5_values"] == [14] * 16
        and fields["volume_values"] == [36] * 16,
        all16_cutoff_values_are16=fields["uninterpreted_candidate_values"] == [16] * 16,
        all16_B_values_equal_fixed_value=[data[48 * step + 8] >> 2 for step in range(16)]
        == [value] * 16,
    )


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in DIRECTORIES]
    registration_path = root / "experiments" / REGISTRATION
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh resonance registration and both folders required")
    folder = root / "experiments/event-064-c-return-sound3-filter-B-lock-down"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    context = json.loads(
        (root / "experiments/sound3-filter-B-range-registration-001.json").read_text()
    )
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Verified independent minimum return required")
    source = load_artifact(source_path)
    base = decode_artifact(source)
    unchanged = source.to_bytes()
    targets = []
    for directory, value in zip(directories, (0, 63)):
        edited = rebuild_labels(source, fixed_packets(base, value))
        edited.metadata["transformations"].append(
            {"kind": "research-fixed-LPF16-B-pair", "B_value": value, "hardware_verified": False}
        )
        target = decode_artifact(edited)
        checks = preservation_checks(base, target, value, context)
        if not all(checks.values()):
            raise ValueError("Generated resonance native preservation failed")
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
            entire_target_body_and_packets_after_wav_decode=actual.encoded_body
            == target.encoded_body
            and actual.packets == target.packets,
            source_preserved=source.to_bytes() == unchanged
            and sha256_file(source_path) == observation["artifact_sha256"],
        )
        report = {
            "analysis_version": "fixed-LPF16-B0-B63-waveform-validation-0.1",
            "hardware_verified": False,
            "passed": all(checks.values()),
            "checks": checks,
            "encoding": encoding,
            "strict_phase_roundtrip": comparison,
            "target_frame": frame_report(target),
        }
        write_bytes(directory / "software-validation.json", json_bytes(report))
        if not report["passed"]:
            raise ValueError("Resonance waveform check failed; outputs retained")
        targets.append(
            {
                "experiment_id": directory.name,
                "raw_B_value": value,
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "restore_wav_sha256": sha256_file(directory / "restore.wav"),
                "edited_artifact_sha256": sha256_file(directory / "edited.symbols.npz"),
                "software_validation_sha256": sha256_file(directory / "software-validation.json"),
            }
        )
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_generated_B0_reference_backup_and_audio"
                    if value == 0
                    else "awaiting_verified_reference_then_generated_B63_backup_and_audio",
                    "restore_file": "restore.wav",
                    "registration": "../" + REGISTRATION,
                    "hardware_restore": {"status": "not_run"},
                    "planned_actions": [
                        "For B63 wait for verified B0 native reception and usable reference audio",
                        "Restore with established stereo setup and level; keep both knobs and audio settings unchanged",
                        "Before ordinary playback save full capture.wav at established reduced level with one second trailing silence",
                        "Select Pattern1/Sound3/FILTER without knob movement; separately record12 to15 seconds ordinary playback as playback.wav, stop/write off",
                        "Report successful restore and actual sound; no WRITE-held pass or required remembered comparison",
                    ],
                }
            ),
        )
    reference, candidate = [
        decode_artifact(load_artifact(path / "edited.symbols.npz")) for path in directories
    ]
    a, b = [bytearray(pattern_data(frame, 1)) for frame in (reference, candidate)]
    for data in (a, b):
        for step in range(16):
            data[48 * step + 8] &= 3
    assert a == b
    original_path = root / "experiments/sound3-generated-pitch13-14-registration-001.json"
    original = json.loads(original_path.read_text())
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "LPF16-generated-resonance-B0-B63-and-tone-preregistration-0.1",
                "hardware_verified": False,
                "registered_before_both_native_captures_and_playback": True,
                "source_artifact": observation["artifact_path"],
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": MINIMUM_BODY,
                "source_observation_sha256": sha256_file(observation_path),
                "candidate": context["candidate"],
                "broader_FILTER_candidate": context["broader_FILTER_candidate"],
                "expected_packet_count": 815,
                "expected_frame_end_byte": 156758,
                "expected_capture_sequence": targets,
                "original_frequency_registration": original_path.relative_to(root).as_posix(),
                "original_frequency_registration_sha256": sha256_file(original_path),
                "frequency_method": original["frequency_method"],
                "resonance_comparison_parameters": {
                    "reference_frequency_lead_hz": 530.26,
                    "frequency_relative_tolerance": 0.005,
                    "loop_seconds_tolerance": 0.005,
                    "minimum_amplitude_increase_fraction": 0.05,
                },
                "hypotheses": {
                    "native": "Both full generated bodies recapture exactly; pair differs only in third-primary bits2..7",
                    "audio": "At fixed cutoff16 the B63 repeated-tone amplitude exceeds B0 by at least5% in all six frozen channel/threshold comparisons, with frequency and loop consistent",
                },
                "limits": [
                    "Both generated targets are new combined cutoff/resonance contexts, not independent recorded whole-body replays",
                    "Amplitude increase is a new hypothesis after endpoint data and before both audio captures; the original common measurement method stays unchanged",
                    "Too-quiet, distorted, insufficient or otherwise unusable audio is retained without changing thresholds, windows or frequency search",
                    "B0 reference must have exact reception and usable near530.26Hz audio before requesting B63",
                    "Only fixed0/63 B at LPF16 from exact minimum source are allowed by research constructor; public cutoff guards remain unchanged",
                    "No all-code resonance law, full bit7 semantics, broad spectral response or public resonance writer is inferred",
                ],
            }
        ),
    )
    print(json.dumps({"passed": True, "hardware_verified": False, "targets": targets}))


if __name__ == "__main__":
    main()
