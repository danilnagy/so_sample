"""Register a full-bar interior FILTER capture and a fixed prior-audio comparison."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes

CAPTURE_ID = "event-058-e-sound3-filter-A-center"
REGISTRATION = "sound3-filter-A-center-registration-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/event-057-d-return-sound3-filter-A-lock-up"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    reference = root / "experiments/edited-sound3-pitch14-001"
    reference_report_path = reference / "pitch-frequency-results-001.json"
    reference_report = json.loads(reference_report_path.read_text())
    original_method_path = root / "experiments/sound3-generated-pitch13-14-registration-001.json"
    original_method = json.loads(original_method_path.read_text())
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(root / observation["artifact_path"]) != observation["artifact_sha256"]
        or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
        or not reference_report["passed"]
        or reference_report["source_sha256"] != sha256_file(reference / "playback.wav")
        or reference_report["parameters"] != original_method["frequency_method"]["parameters"]
        or reference_report["registration_sha256"] != sha256_file(original_method_path)
    ):
        raise ValueError("Verified exact FILTER return and pinned prior playback required")
    directory = root / "experiments" / CAPTURE_ID
    registration_path = root / "experiments" / REGISTRATION
    if directory.exists() or directory.is_symlink() or registration_path.exists():
        raise ValueError("Fresh center registration and directory required")
    directory.mkdir()
    limits = [
        "Interior raw value and whole target body are unknown;31/32 or uniformity are not predicted",
        "Raw between-endpoint tests concern two monotonic scalar interpretations only; passing/failing them does not settle all mode/flag models",
        "Reference audio already exists from before FILTER recording; new comparison is registered before center data, with the original common frequency method unchanged",
        "Near-reference tone amplitude is a5% hypothesis at the repeated component, not proof of broadband bypass or a complete filter law",
        "Tone frequency and loop must stay consistent; failures or ramps are retained without fitting new windows, thresholds or endpoint codes",
        "No numeric UI, digital silence, resonance or filter writer is inferred; other third-byte bits stay opaque",
    ]
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "FILTER-A-full-bar-center-and-prior-audio-preregistration-0.1",
                "registered_before_center_backup_and_audio": True,
                "reference_audio_already_observed": True,
                "hardware_verified": False,
                "experiment_id": CAPTURE_ID,
                "source_artifact": observation["artifact_path"],
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": observation["body_sha256"],
                "source_observation_sha256": sha256_file(observation_path),
                "expected_packet_count": 815,
                "expected_frame_end_byte": 156758,
                "candidate": {
                    "pattern": 1,
                    "sound": 3,
                    "second_primary_mask": 240,
                    "third_primary_mask": 3,
                },
                "broader_FILTER_candidate": {"second_primary_mask": 240, "third_primary_mask": 255},
                "contiguous_endpoint_values": [1, 62],
                "alternative_endpoint_values": [4, 59],
                "monotonic_scalar_hypotheses": {
                    "contiguous": "Interior projected values should lie strictly between1 and62",
                    "alternative": "Interior projected values should lie strictly between4 and59",
                },
                "expected_pitch_values": [14] * 16,
                "expected_volume_values": [36] * 16,
                "expected_interior_raw_code": None,
                "reference_audio": (reference / "playback.wav").relative_to(root).as_posix(),
                "reference_audio_sha256": sha256_file(reference / "playback.wav"),
                "reference_audio_results": reference_report_path.relative_to(root).as_posix(),
                "reference_audio_results_sha256": sha256_file(reference_report_path),
                "original_frequency_registration": original_method_path.relative_to(
                    root
                ).as_posix(),
                "original_frequency_registration_sha256": sha256_file(original_method_path),
                "frequency_method": original_method["frequency_method"],
                "neutral_comparison_parameters": {
                    "amplitude_relative_tolerance": 0.05,
                    "frequency_relative_tolerance": 0.005,
                    "loop_seconds_tolerance": 0.005,
                },
                "recorded_action": "While Pattern1/Sound3/FILTER plays hold WRITE and move only A from maximum toward midpoint until bottom bar is full and sample clearest, about5 seconds; hold3 seconds stationary then release/stop/write off",
                "limits": limits,
            }
        ),
    )
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": CAPTURE_ID,
                "capture_status": "awaiting_recorded_FILTER_center_backup_and_ordinary_playback",
                "registration": "../" + REGISTRATION,
                "planned_actions": [
                    "Keep Pattern1/Sound3/FILTER, B and all audio settings unchanged",
                    "Start playback, hold WRITE and move only A toward midpoint over about5 seconds until display bottom bar full and sample clearest; hold3 seconds stationary",
                    "Release WRITE, stop and ensure write off; save complete capture.wav at established reduced level with one second tail",
                    "Separately record12 to15 seconds of ordinary Pattern1 playback as playback.wav; then stop/write off",
                    "Report whether sample audible and bar full; exact code unknown, no numeric display inferred; leave A at center and B untouched",
                ],
            }
        ),
    )
    write_bytes(
        directory / "instructions.md",
        b"# Recorded FILTER A center\n\nKeep Pattern 1 / Sound 3 / FILTER, B and all audio settings unchanged. Start\nplayback, hold WRITE and move only A counterclockwise toward the midpoint\nover about 5 seconds, stopping where the bottom bar is full and the sample\nsounds clearest. Hold WRITE3 more seconds with knobs stationary, then release\nWRITE, stop and ensure write off. Do not press keyboard keys or hold BPM/FX.\n\nBefore ordinary playback, save a full backup here as capture.wav at the established\nreduced level with one second trailing silence. Separately record12 to15 seconds\nof ordinary Pattern1 playback as playback.wav, then stop/write off. Confirm\nwhether sample is audible and bar full. Leave A at center and B untouched.\nNo restore needed; no exact numeric center code is assumed.\n",
    )
    print(
        json.dumps({"registered": True, "next_capture": CAPTURE_ID, "interior_code_unknown": True})
    )


if __name__ == "__main__":
    main()
