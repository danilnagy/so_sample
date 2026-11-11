"""Prepare fixed pitch13/14 research WAVs and freeze the frequency test before audio."""

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
from scripts.check_sound3_tone_pitch_probe import location_report
from scripts.check_sound3_tone_pitch_range import first_mask_preserved

MINIMUM_BODY = "227d4d25e644c83f2d8e89d2a4135125f8cb926082983a81b4842de21e654fc2"
DIRECTORIES = ("edited-sound3-pitch13-reference-001", "edited-sound3-pitch14-001")
REGISTRATION = "sound3-generated-pitch13-14-registration-001.json"


def fixed_packets(frame, value):
    if hashlib.sha256(frame.encoded_body).hexdigest() != MINIMUM_BODY:
        raise ValueError("Exact genuine uniform1 minimum required")
    if type(value) is not int or value not in (13, 14):
        raise ValueError("Only fixed research values13 and14 are allowed")
    data = bytearray(pattern_data(frame, 1))
    for step in range(16):
        p = 48 * step + 6
        if (data[p] & 63) != 1:
            raise ValueError("Uniform1 minimum source required")
        data[p] = (data[p] & 224) | value
    return _replace_pattern_data(frame, 1, bytes(data))


def pair_preservation(base, target, value):
    context = {
        "source_body_sha256": MINIMUM_BODY,
        "expected_packet_count": 815,
        "expected_frame_end_byte": 156758,
        "expected_tempo_bpm": 100,
        "expected_swing_byte": 9,
    }
    report = location_report(base, target, context)
    data = pattern_data(target, 1)
    return dict(
        report["preservation_checks"],
        **report["control_checks"],
        only_first_low5_bits_changed=first_mask_preserved(base, target, 31),
        all16_fields_equal_fixed_value=[data[48 * step + 6] & 63 for step in range(16)]
        == [value] * 16,
        all16_volume_values_stay36=report["raw_sound3_fields"]["after"]["known_volume_values"]
        == [36] * 16,
    )


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in DIRECTORIES]
    registration_path = root / "experiments" / REGISTRATION
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh registration and both output directories required")
    folder = root / "experiments/event-053-d-return-sound3-tone-pitch-lock-minimum"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Verified exact independent minimum return required")
    source = load_artifact(source_path)
    base = decode_artifact(source)
    unchanged = source.to_bytes()
    legs = []
    for directory, value in zip(directories, (13, 14)):
        edited = rebuild_labels(source, fixed_packets(base, value))
        edited.metadata["transformations"].append(
            {"kind": "research-fixed-Sound3-pitch", "raw_value": value, "hardware_verified": False}
        )
        target = decode_artifact(edited)
        checks = pair_preservation(base, target, value)
        if not all(checks.values()):
            raise ValueError("Pitch pair native preservation failed")
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
            entire_target_body_after_wav_decode=actual.encoded_body == target.encoded_body,
            entire_target_packets_after_wav_decode=actual.packets == target.packets,
            source_artifact_preserved=source.to_bytes() == unchanged,
            source_file_preserved=sha256_file(source_path) == observation["artifact_sha256"],
        )
        report = {
            "analysis_version": "fixed-pitch13-14-waveform-validation-0.1",
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
            raise ValueError("Pitch waveform check failed; outputs retained")
        legs.append(
            {
                "experiment_id": directory.name,
                "raw_pitch_value": value,
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "edited_artifact_sha256": report["edited_artifact_sha256"],
                "software_validation_sha256": sha256_file(directory / "software-validation.json"),
            }
        )
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_generated13_reference_restore_backup_and_audio"
                    if value == 13
                    else "awaiting_verified_reference_then_generated14_restore_backup_and_audio",
                    "restore_file": "restore.wav",
                    "registration": "../" + REGISTRATION,
                    "hardware_restore": {"status": "not_run"},
                    "planned_actions": [
                        "For14 wait until13 reception and usable audio are verified",
                        "Restore with established stereo path/playback level; keep both knobs and audio settings unchanged",
                        "Pattern1/Sound3/TONE stopped/write off; before playback save full capture.wav at reduced level with one second tail",
                        "Separately record12 to15 seconds of ordinary Pattern1 playback as playback.wav, then stop/write off",
                        "Confirm successful restore and recognizable phrase; no numeric display or remembered pitch comparison required",
                    ],
                }
            ),
        )
    parameters = {
        "center_frequency_hz": 525.0,
        "half_bandwidth_hz": 75.0,
        "envelope_seconds": 0.005,
        "threshold_peak_fractions": [0.15, 0.25, 0.35],
        "minimum_region_seconds": 0.06,
        "edge_margin_seconds": 0.03,
        "minimum_band_rms": 0.001,
        "maximum_gap_residual_seconds": 0.006,
        "threshold_gap_spread_seconds": 0.004,
        "stereo_onset_tolerance_seconds": 0.002,
        "nominal_loop_seconds": 2.4,
        "loop_tolerance_seconds": 0.005,
        "steady_fit_window_after_onset_seconds": [0.08, 0.18],
        "frequency_search_hz": [465.0, 585.0],
        "fft_grid_max_spacing_hz": 0.25,
        "fft_peak_refine_halfwidth_hz": 1.0,
        "minimum_fit_explained_variance": 0.9,
        "minimum_complete_cycles": 3,
        "reference_frequency_lead_hz": 500.65,
        "reference_frequency_relative_tolerance": 0.005,
        "minimum_relative_frequency_increase": 0.005,
        "hypothesized_ratio_for_one_semitone": 2 ** (1 / 12),
        "semitone_ratio_relative_tolerance": 0.002,
        "unchanged_loop_seconds_tolerance": 0.005,
    }
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "generated-pitch13-14-pair-and-frequency-preregistration-0.1",
                "registered_before_both_backups_and_audio": True,
                "hardware_verified": False,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": MINIMUM_BODY,
                "source_observation_sha256": sha256_file(observation_path),
                "range_results_sha256": sha256_file(
                    root / "experiments/sound3-tone-pitch-range-results-001.json"
                ),
                "expected_capture_sequence": legs,
                "frequency_method": {
                    "parameters": parameters,
                    "algorithm": "Common450..600Hz third-order zero-phase band; frozen onset thresholds; fit80..180ms after each onset; Hann FFT with spacing<=0.25Hz selects global peak in465..585Hz, refine least-squares sine/cos/DC within1Hz; identical method for both legs",
                },
                "hypotheses": {
                    "generated14_vs13": "Repeated Sound3 tone frequency increases with unchanged sample codes,keys,volume36 and pattern loop",
                    "one_semitone": "Candidate/reference frequency ratio equals2^(1/12) within0.2% in all six channel/threshold comparisons",
                    "reference": "Generated13 note parameters reproduce the prior measured reference near500.65Hz; parameter-only cells now also13, so this is a generated reference, not a complete genuine-body replay",
                },
                "limits": [
                    "Frequency law is a new hypothesis selected after native endpoint data, before either pair audio",
                    "Both data sets use the same wide band/FFT search without fitting around a presumed candidate frequency",
                    "First verify13 reception and usable audio before requesting14 restoration; failed methods remain retained without rescue",
                    "Only fixed13/14 and exact genuine minimum are accepted by research constructor; no public pitch setter",
                    "One interval does not establish every code's semitone law, full field width or a numeric UI scale",
                ],
            }
        ),
    )
    print(json.dumps({"passed": True, "legs": legs, "hardware_verified": False}))


if __name__ == "__main__":
    main()
