"""Register stopped-repeat and ordinary-playback controls for opaque global131."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes

REGISTRATION = "pattern1-playback-global-registration-001.json"
CAPTURE_IDS = (
    "event-069-a-pattern1-stopped-repeat",
    "event-070-b-pattern1-plain-playback",
)


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    source_folder = root / "experiments/event-068-d-pattern1-FX16-clear-corrected"
    observation_path = source_folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    if not observation["hardware_verified"] or not all(observation["checks"].values()):
        raise ValueError("Accepted corrected clear source required")
    source_artifact = root / observation["artifact_path"]
    source_capture = source_folder / "capture.wav"
    if (
        sha256_file(source_artifact) != observation["artifact_sha256"]
        or sha256_file(source_capture) != observation["capture_sha256"]
    ):
        raise ValueError("Accepted source identity differs")
    registration_path = root / "experiments" / REGISTRATION
    folders = [root / "experiments" / name for name in CAPTURE_IDS]
    if any(path.exists() or path.is_symlink() for path in [registration_path, *folders]):
        raise ValueError("Fresh registration and control folders required")
    actions = [
        [
            "Keep Pattern1 selected, playback stopped, write off; leave both knobs and settings untouched",
            "Without playing first, record a NEW complete backup as capture.wav",
        ],
        [
            "After the first backup, ensure playback stopped and write off",
            "Press PLAY, let Pattern1 run for approximately five seconds, then press PLAY to stop",
            "Do not press FX or turn knobs; record a NEW complete backup as capture.wav",
        ],
    ]
    registration = {
        "analysis_version": "opaque-global131-repeat-and-plain-playback-registration-0.1",
        "hardware_verified": False,
        "registered_before_data_available": True,
        "source_artifact": observation["artifact_path"],
        "source_artifact_sha256": observation["artifact_sha256"],
        "source_capture": source_capture.relative_to(root).as_posix(),
        "source_capture_sha256": observation["capture_sha256"],
        "source_body_sha256": observation["body_sha256"],
        "source_observation": observation_path.relative_to(root).as_posix(),
        "source_observation_sha256": sha256_file(observation_path),
        "expected_packet_count": 815,
        "expected_frame_end_byte": 156758,
        "global_candidate": {
            "packet_index": 2,
            "tag": 32092,
            "payload_offset": 131,
            "narrow_mask": 15,
            "broader_mask": 255,
        },
        "expected_footer_hex": "ffffffffffffffff",
        "expected_capture_sequence": [
            {
                "experiment_id": name,
                "planned_actions": action,
                "expected_global_byte": 7 if index == 0 else None,
            }
            for index, (name, action) in enumerate(zip(CAPTURE_IDS, actions))
        ],
        "predictions": {
            "stopped_repeat_entire_body_equal_source": True,
            "plain_playback_preserves_every_byte_except_global131_low4": True,
            "plain_playback_global_value_or_change": None,
        },
        "limits": [
            "No FX action or write pass; all sixteen Pattern1 footer nibbles must stay F",
            "Stopped-repeat exact equality is a hypothesis; retain any independent counterexample",
            "Keep low-four scope and broader whole-byte diagnostic separate; do not widen after data",
            "Different WAVs may legitimately decode to identical native bodies; copied raw WAVs are not independent controls",
            "A playback-associated change would not establish an effect selector, step index, nibble order, or public writer",
        ],
    }
    write_bytes(registration_path, json_bytes(registration))
    for folder, action in zip(folders, actions):
        folder.mkdir()
        write_bytes(
            folder / "experiment.json",
            json_bytes(
                {
                    "experiment_id": folder.name,
                    "capture_status": "awaiting_capture",
                    "registration": "../" + REGISTRATION,
                    "planned_actions": action,
                }
            ),
        )
        write_bytes(
            folder / "instructions.md",
            (
                "# Opaque global-byte control\n\n"
                + "\n".join(f"{index}. {item}" for index, item in enumerate(action, 1))
                + "\n\nUse the established reduced recording level, complete dump and one second trailing silence.\n"
            ).encode(),
        )
    print(json.dumps({"registered": True, "capture_folders": list(CAPTURE_IDS)}))


if __name__ == "__main__":
    main()
