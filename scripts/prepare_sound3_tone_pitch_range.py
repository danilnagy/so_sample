"""Preregister unknown upper pitch data and an exact return to observed uniform1."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact

CAPTURE_IDS = (
    "event-052-c-sound3-tone-pitch-lock-up",
    "event-053-d-return-sound3-tone-pitch-lock-minimum",
)
REGISTRATION = "sound3-tone-pitch-range-registration-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    source_folder = root / "experiments/event-051-b-sound3-tone-pitch-lock-down"
    observation_path = source_folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    source = decode_artifact(load_artifact(source_path))
    data = pattern_data(source, 1)
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(source_folder / "capture.wav") != observation["capture_sha256"]
        or [data[48 * step + 6] & 63 for step in range(16)] != [1] * 16
        or [(data[48 * step + 6] >> 6) | ((data[48 * step + 7] & 15) << 2) for step in range(16)]
        != [36] * 16
    ):
        raise ValueError("Verified uniform1 minimum with volume36 required")
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    registration_path = root / "experiments" / REGISTRATION
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh range registration and capture folders required")
    legs = [
        {
            "experiment_id": CAPTURE_IDS[0],
            "knob_action": "recorded_A_clockwise_to_physical_maximum",
            "expected_endpoint_code": None,
        },
        {
            "experiment_id": CAPTURE_IDS[1],
            "knob_action": "recorded_A_counterclockwise_to_physical_minimum",
            "expected_endpoint_code": 1,
            "expected_complete_body_sha256": observation["body_sha256"],
        },
    ]
    limits = [
        "Upper endpoint code is unknown and not guessed from the lower result or a presumed semitone scale",
        "Exact return to uniform1 and the whole independent minimum body is a new prediction registered before both data captures",
        "First-low6 and narrower first-low5 mask alternatives are tested separately; unused bit5 does not prove field width",
        "Broader TONE/auxiliary changes remain visible; no widening of the strict mask to claim success",
        "Movement can retain ramps; maximum uniformity is diagnostic, not a required endpoint or a fitted average",
        "No pitch-field writer, numeric UI reading, frequency ratio or semitone law is confirmed",
    ]
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "recorded-TONE-A-upper-and-exact-minimum-return-preregistration-0.1",
                "registered_before_both_captures": True,
                "hardware_verified": False,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (source_folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": observation["body_sha256"],
                "source_observation_sha256": sha256_file(observation_path),
                "expected_packet_count": 815,
                "expected_frame_end_byte": 156758,
                "expected_tempo_bpm": 100,
                "expected_swing_byte": 9,
                "expected_capture_sequence": legs,
                "candidate": {
                    "pattern": 1,
                    "sound": 3,
                    "first_low6_mask": 63,
                    "narrower_first_low5_mask": 31,
                    "all16_cells": True,
                },
                "expected_volume_values": [36] * 16,
                "expected_audition_sequence": [
                    "higher_during_upward_pass",
                    "lower_during_return_pass",
                ],
                "display_numeric_values_assumed": None,
                "limits": limits,
            }
        ),
    )
    for directory, leg in zip(directories, legs):
        directory.mkdir()
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_recorded_A_maximum"
                    if directory == directories[0]
                    else "awaiting_recorded_A_return_minimum_after_maximum",
                    "registration": "../" + REGISTRATION,
                    "registered_leg": leg,
                    "planned_actions": [
                        "Keep Pattern1/Sound3/TONE, B and all audio settings unchanged",
                        "While Pattern1 plays hold WRITE and turn only A to this leg's physical endpoint over about5 seconds",
                        "Hold WRITE3 more seconds stationary, release WRITE, stop playback and ensure write off",
                        "Save a complete capture.wav at established reduced level with one second tail; save the maximum capture before beginning the minimum return",
                        "Report audible pitch direction and any display text actually seen; after final return leave A at minimum and B untouched",
                    ],
                }
            ),
        )
    print(json.dumps({"registered": True, "legs": legs, "hardware_verified": False}))


if __name__ == "__main__":
    main()
