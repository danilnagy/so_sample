"""Register the unknown counterclockwise FILTER endpoint and an exact clockwise return."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact

CAPTURE_IDS = (
    "event-056-c-sound3-filter-A-lock-down",
    "event-057-d-return-sound3-filter-A-lock-up",
)
REGISTRATION = "sound3-filter-A-range-registration-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/event-055-b-sound3-filter-A-lock-up"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    source = decode_artifact(load_artifact(source_path))
    data = pattern_data(source, 1)
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
        or [(data[48 * step + 7] >> 4) | ((data[48 * step + 8] & 3) << 4) for step in range(16)]
        != [62] * 16
    ):
        raise ValueError("Verified uniform contiguous62 clockwise source required")
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    registration_path = root / "experiments" / REGISTRATION
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh FILTER range registration and both folders required")
    legs = [
        {
            "experiment_id": CAPTURE_IDS[0],
            "action": "record_only_A_counterclockwise_to_physical_minimum",
            "expected_endpoint_code": None,
        },
        {
            "experiment_id": CAPTURE_IDS[1],
            "action": "record_only_A_clockwise_to_physical_maximum",
            "expected_contiguous_values": [62] * 16,
            "expected_alternative_values": [59] * 16,
            "expected_complete_body_sha256": observation["body_sha256"],
        },
    ]
    limits = [
        "Counterclockwise endpoint code and resulting body are unknown; no zero, cutoffHz or low-pass numeric value is guessed",
        "Exact return to the complete independent clockwise body is registered before both captures",
        "Contiguous grouping and high-nibble-as-more-significant grouping remain alternative projections; bit order and filter law are not chosen from one endpoint",
        "Strict candidate masks are frozen; broader third-byte/primary/auxiliary alternatives retain coupled or wider changes without rescuing strict support",
        "Ramps and nonuniform endpoint values are retained literally; no average is used as an endpoint",
        "User-described high-pass/inaudibility and bar display are qualitative evidence, not a digital-silence measurement or numeric UI value",
        "No resonance field, filter writer or extension of existing pitch/volume guards is enabled",
    ]
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "FILTER-A-counterclockwise-and-exact-clockwise-return-preregistration-0.1",
                "registered_before_both_captures": True,
                "hardware_verified": False,
                "source_artifact": source_path.relative_to(root).as_posix(),
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
                "expected_capture_sequence": legs,
                "expected_pitch_values": [14] * 16,
                "expected_volume_values": [36] * 16,
                "raw_projections": {
                    "contiguous": "(second_primary>>4) | ((third_primary&3)<<4)",
                    "high_nibble_more_significant": "((second_primary>>4)<<2) | (third_primary&3)",
                },
                "display_numeric_values_assumed": None,
                "limits": limits,
            }
        ),
    )
    for index, directory in enumerate(directories):
        directory.mkdir()
        direction = "counterclockwise to minimum" if index == 0 else "clockwise to maximum"
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_recorded_FILTER_A_counterclockwise"
                    if index == 0
                    else "awaiting_recorded_FILTER_A_clockwise_return_after_counterclockwise",
                    "registration": "../" + REGISTRATION,
                    "registered_leg": legs[index],
                    "planned_actions": [
                        "Keep Pattern1/Sound3/FILTER, B and all audio settings unchanged",
                        f"During playback hold WRITE and move only A fully {direction} over5 seconds, then hold3 seconds stationary",
                        "Release WRITE, stop and ensure write off before full capture.wav at reduced level with one second tail",
                        "Save counterclockwise capture before starting clockwise return; no keyboard keys or BPM/FX during passes",
                        "Report sound and display changes actually observed, including whether sample becomes audible during movement; after return leave A maximum and B untouched",
                    ],
                }
            ),
        )
        write_bytes(
            directory / "instructions.md",
            (
                f"# FILTER A {direction}\n\nKeep Pattern 1 / Sound 3 / FILTER, B and all audio settings unchanged.\nStart playback, hold WRITE and turn only A fully {direction}\nover about5 seconds. Hold WRITE3 more seconds stationary, release WRITE,\nstop playback and ensure write off. Do not press keyboard keys or hold BPM/FX.\nSave a full backup here as capture.wav at the established reduced recording\nlevel with one second trailing silence. Save the counterclockwise backup\nbefore beginning the clockwise return. No restore or separate audio recording\nis needed. Report audible/display changes actually observed. After both\npasses leave A at maximum and B untouched.\n"
            ).encode(),
        )
    print(json.dumps({"registered": True, "legs": legs, "hardware_verified": False}))


if __name__ == "__main__":
    main()
