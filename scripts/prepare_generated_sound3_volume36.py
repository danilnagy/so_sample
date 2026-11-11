"""Prepare a fixed upper-interior reciprocal probe; no public volume setter."""

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
from scripts.check_sound3_volume_middle_series import broad_preservation
from scripts.prepare_generated_sound3_volume18_pair import REFERENCE_BODY

DIRECTORY = "edited-sound3-volume36-002"
REGISTRATION = "sound3-generated-volume36-registration-002.json"


def candidate_packets(frame):
    """Exact uniform21 source only; fixed36 (alternate9), all16 Sound3/P1 cells."""
    if hashlib.sha256(frame.encoded_body).hexdigest() != REFERENCE_BODY:
        raise ValueError("Exact independently verified uniform21 source required")
    data = bytearray(pattern_data(frame, 1))
    for step in range(16):
        p = 48 * step + 6
        if (data[p] >> 6) | ((data[p + 1] & 15) << 2) != 21:
            raise ValueError("All16 source fields must equal21")
        data[p] &= 0x3F
        data[p + 1] = (data[p + 1] & 0xF0) | 9
    return _replace_pattern_data(frame, 1, bytes(data))


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if directory.exists() or directory.is_symlink() or registration_path.exists():
        raise ValueError("Fresh candidate directory and registration required")
    reference = root / "experiments/replayed-sound3-volume21-reference-001"
    method_path = root / "experiments/sound3-volume18-gain-method-registration-001.json"
    gain_path = root / "experiments/sound3-generated-volume18-gain-results-001.json"
    previous_observation_path = (
        root / "experiments/edited-sound3-volume18-001/hardware-observation-001.json"
    )
    observation_path = reference / "hardware-observation-001.json"
    observation, previous_observation, gain = [
        json.loads(path.read_text())
        for path in (observation_path, previous_observation_path, gain_path)
    ]
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not previous_observation["hardware_verified"]
        or not all(observation["checks"].values())
        or not all(previous_observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(reference / "capture.wav") != observation["capture_sha256"]
        or sha256_file(gain_path) != previous_observation["gain_results_sha256"]
        or not gain["all_contiguous_order_gain_directions_supported"]
    ):
        raise ValueError("Verified reference and original generated18 evidence required")
    source = load_artifact(source_path)
    base = decode_artifact(source)
    unchanged = source.to_bytes()
    edited = rebuild_labels(source, candidate_packets(base))
    edited.metadata["transformations"].append(
        {
            "kind": "research-fixed-reciprocal-volume36-probe",
            "contiguous_raw_code": 36,
            "alternative_order_raw_code": 9,
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    after = pattern_data(target, 1)
    checks = dict(
        broad_preservation(base, target),
        source_body_is_exact_uniform21=hashlib.sha256(base.encoded_body).hexdigest()
        == REFERENCE_BODY,
        all16_fields_are_contiguous36_and_alternative9=all(
            ((after[48 * step + 6] >> 6) | ((after[48 * step + 7] & 15) << 2)) == 36
            and (((after[48 * step + 6] >> 6) << 4) | (after[48 * step + 7] & 15)) == 9
            for step in range(16)
        ),
        native_geometry_exact=len(target.packets) == 815 and target.end_byte == 156758,
        source_artifact_preserved=source.to_bytes() == unchanged,
    )
    if not all(checks.values()):
        raise ValueError("Fixed36 native preservation checks failed")
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
        source_file_preserved=sha256_file(source_path) == observation["artifact_sha256"],
    )
    report = {
        "analysis_version": "fixed-volume36-reciprocal-probe-software-validation-0.1",
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
        raise ValueError("Fixed36 waveform failed; outputs retained")
    leg = {
        "experiment_id": DIRECTORY,
        "contiguous_raw_code": 36,
        "alternative_order_raw_code": 9,
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "restore_wav_sha256": report["restore_wav_sha256"],
        "edited_artifact_sha256": report["edited_artifact_sha256"],
        "software_validation_sha256": sha256_file(directory / "software-validation.json"),
        "backup_file": "capture.wav",
        "ordinary_playback_file": "playback.wav",
    }
    reference_pair = json.loads(
        (root / "experiments/sound3-generated-volume18-pair-registration-001.json").read_text()
    )
    registration = {
        "analysis_version": "fixed-volume36-reciprocal-preregistration-0.1",
        "hardware_verified": False,
        "registered_before_candidate_capture_and_audio": True,
        "reference_already_observed": True,
        "selected_after_original_volume18_result": True,
        "source_artifact": source_path.relative_to(root).as_posix(),
        "source_artifact_sha256": observation["artifact_sha256"],
        "source_capture": (reference / "capture.wav").relative_to(root).as_posix(),
        "source_capture_sha256": observation["capture_sha256"],
        "source_body_sha256": REFERENCE_BODY,
        "source_observation_sha256": sha256_file(observation_path),
        "prior_generated18_observation_sha256": sha256_file(previous_observation_path),
        "prior_generated18_gain_results_sha256": sha256_file(gain_path),
        "gain_measurement_registration": method_path.relative_to(root).as_posix(),
        "gain_measurement_registration_sha256": sha256_file(method_path),
        "reference_audio": (reference / "playback.wav").relative_to(root).as_posix(),
        "reference_audio_sha256": sha256_file(reference / "playback.wav"),
        "reference_audio_results_sha256": sha256_file(reference / "playback-gain-results-001.json"),
        "expected_capture_sequence": [reference_pair["expected_capture_sequence"][0], leg],
        "gain_hypotheses": {
            "contiguous_order": "36>21: repeated Sound3 tone amplitude should increase",
            "alternative_order": "9<21: repeated Sound3 tone amplitude should decrease",
            "minimum_relative_amplitude_difference": 0.03,
            "unchanged_pitch_relative_tolerance": 0.005,
            "unchanged_loop_seconds_tolerance": 0.005,
        },
        "limits": [
            "This complementary test is selected after observing the original lower-interior result; all new data remain pending",
            "Reuse the original reference audio and exactly frozen tone measurement; no new fit or gain law",
            "All six comparisons must support the direction with stable pitch and loop; unchanged recording settings are required",
            "Subjective relative loudness is optional and an uncertain impression must not become a confirmed observation",
            "No public volume writer or every-value calibration; software remains hardware unverified",
        ],
    }
    write_bytes(registration_path, json_bytes(registration))
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_generated36_restore_backup_and_audio",
                "restore_file": "restore.wav",
                "registration": "../" + REGISTRATION,
                "hardware_restore": {"status": "not_run"},
                "planned_actions": [
                    "Restore complete waveform with established stereo path and playback level; keep both knobs and all audio settings unchanged",
                    "Pattern1/Sound3/TONE stopped/write off; before playback save complete capture.wav with established reduced recording level and one second tail",
                    "Separately record12 to15 seconds of ordinary Pattern1 playback as playback.wav, then stop/write off",
                    "Confirm restore success and recognizable phrase; relative loudness may be reported as uncertain without guessing; keep knobs untouched",
                ],
            }
        ),
    )
    print(json.dumps({"passed": True, "candidate": leg, "hardware_verified": False}))


if __name__ == "__main__":
    main()
