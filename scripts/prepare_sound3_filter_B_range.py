"""Register an unknown FILTER B maximum and an exact minimum return."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes

CAPTURE_IDS = (
    "event-063-b-sound3-filter-B-lock-up",
    "event-064-c-return-sound3-filter-B-lock-down",
)
REGISTRATION = "sound3-filter-B-range-registration-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/event-062-a-sound3-filter-B-lock-down"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    previous = json.loads(
        (root / "experiments/sound3-filter-B-minimum-registration-001.json").read_text()
    )
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or observation["contiguous_B_candidate_values"] != [0] * 16
        or sha256_file(root / observation["artifact_path"]) != observation["artifact_sha256"]
        or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Verified literal B0 minimum required")
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    registration_path = root / "experiments" / REGISTRATION
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh B range registration and both capture directories required")
    legs = [
        {
            "experiment_id": CAPTURE_IDS[0],
            "action": "record_only_B_clockwise_to_maximum",
            "expected_endpoint_code": None,
        },
        {
            "experiment_id": CAPTURE_IDS[1],
            "action": "record_only_B_counterclockwise_to_minimum",
            "expected_complete_body_sha256": observation["body_sha256"],
            "expected_five_bit_values": [0] * 16,
            "expected_six_bit_values": [0] * 16,
        },
    ]
    registration = {
        name: previous[name]
        for name in (
            "expected_packet_count",
            "expected_frame_end_byte",
            "candidate",
            "broader_FILTER_candidate",
            "B_candidate_masks",
            "expected_pitch_values",
            "expected_volume_values",
            "expected_filter_A_values",
        )
    }
    registration.update(
        analysis_version="FILTER-B-unknown-maximum-and-exact-minimum-return-preregistration-0.1",
        hardware_verified=False,
        registered_before_both_captures=True,
        source_artifact=observation["artifact_path"],
        source_artifact_sha256=observation["artifact_sha256"],
        source_capture=(folder / "capture.wav").relative_to(root).as_posix(),
        source_capture_sha256=observation["capture_sha256"],
        source_body_sha256=observation["body_sha256"],
        source_observation_sha256=sha256_file(observation_path),
        source_results_sha256=observation["native_results_sha256"],
        expected_capture_sequence=legs,
        limits=[
            "Maximum endpoint and body are unknown; no63, range, uniformity or audible change is predicted",
            "Exact return to entire independent minimum body and every packet is registered before both captures",
            "Narrow mask0x7c failed at the first minimum because bit7 changed; original failed report remains immutable; both masks and projections stay separate",
            "All stored A63, pitch14, volume36 and noncandidate state must be preserved under the six-bit mask; wider snapshots are retained without rescue",
            "No audible change is acceptable at neutral cutoff; no resonance law or bit7 role is inferred from endpoints alone",
            "Public filter guards remain unchanged and reject this new third-byte context; no resonance writer is enabled",
        ],
    )
    write_bytes(registration_path, json_bytes(registration))
    for directory, direction in zip(directories, ("clockwise", "counterclockwise")):
        directory.mkdir()
        actions = [
            "Keep Pattern1/Sound3/FILTER, A and audio settings unchanged",
            f"Start playback, hold WRITE and move only B fully {direction} over5 seconds; hold WRITE3 more seconds stationary",
            "Release WRITE, stop and ensure write off; save full capture.wav here at established reduced level with one second trailing silence before the next action",
            "Report actual audible/display changes or no change; no restore or separate playback recording required",
        ]
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_recorded_FILTER_B_range_control",
                    "registration": "../" + REGISTRATION,
                    "planned_actions": actions,
                }
            ),
        )
        write_bytes(
            directory / "instructions.md",
            (
                "# Recorded FILTER B range control\n\n"
                + "\n".join(f"{index}. {action}" for index, action in enumerate(actions, 1))
                + "\n\nDo not press keyboard keys or hold BPM/FX. After both captures leave B at minimum and A untouched.\n"
            ).encode(),
        )
    print(json.dumps({"registered": True, "next_captures": list(CAPTURE_IDS)}))


if __name__ == "__main__":
    main()
