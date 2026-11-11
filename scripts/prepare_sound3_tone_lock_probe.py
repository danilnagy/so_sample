"""Register plain playback followed by a Sound3 TONE lock pass without guessing bitfields."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact

CAPTURE_IDS = ("event-043-a-sound3-plain-playback", "event-044-b-sound3-tone-volume-lock-up")


def main():
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    registration_path = root / "experiments/sound3-tone-lock-probe-registration-001.json"
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh registration and capture directories required")
    baseline = root / "experiments/event-042-b-sound3-tone-volume-minimum"
    observation_path = baseline / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or observation["audition_result"] != "quieter_not_silent"
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Verified unchanged live-volume minimum and audible observation required")
    frame = decode_artifact(load_artifact(source_path))
    data = pattern_data(frame, 1)
    if frame.packets[2].payload[129:131] != bytes([100, 9]):
        raise ValueError("Expected current100 BPM/swing9")
    records = [
        {
            "step": step,
            "primary_hex": data[48 * (step - 1) + 6 : 48 * (step - 1) + 9].hex(),
            "auxiliary_byte": data[768 + 16 * (step - 1) + 2],
        }
        for step in range(1, 17)
    ]
    registration = {
        "analysis_version": "sound3-plain-playback-and-tone-lock-up-preregistration-0.1",
        "registered_before_all_captures": True,
        "hardware_verified": False,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": observation["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_capture_sha256": observation["capture_sha256"],
        "baseline_body_sha256": observation["body_sha256"],
        "baseline_observation_sha256": sha256_file(observation_path),
        "expected_tempo_bpm": 100,
        "expected_swing_byte": 9,
        "baseline_sound3_pattern1_cells": records,
        "expected_capture_sequence": [
            {
                "experiment_id": CAPTURE_IDS[0],
                "action": "Pattern1/Sound3/TONE; plain playback for about3 seconds with write off and both knobs untouched, then stop and capture",
                "expected_body_sha256_if_plain_playback_is_not_serialized": observation[
                    "body_sha256"
                ],
            },
            {
                "experiment_id": CAPTURE_IDS[1],
                "action": "Play Pattern1; hold WRITE and turn only B clockwise to maximum over about5 seconds; hold WRITE another3 seconds with knobs stationary; release WRITE, stop, ensure write off, then capture",
                "expected_body_sha256": None,
            },
        ],
        "location_hypotheses": {
            "plain_playback_does_not_change_native_body": "FreshA is tested against genuine pre-audition minimum state, not assumed identical",
            "tone_lock_changes_only_pattern1_sound3_primary_cells": "All16 Sound3 primary cells are candidates, including previously empty steps; each3-byte tuple remains opaque",
            "tone_lock_changes_only_pattern1_sound3_primary_and_auxiliary_cells": "Broader alternative retained separately; existing keys and event flags are not presumed unchanged",
            "tone_lock_no_serialized_change": "Retain as possible failed/ineffective lock or nonserialized action; do not repair data to force a change",
            "volume_specific_bitfield_and_numeric_maximum_unknown": True,
        },
        "official_control_reference": "https://teenage.engineering/guides/po-33/en",
        "limits": [
            "Official guide specifies WRITE plus knob movement while playing to record TONE/FILTER parameters for selected sound",
            "Only B is intentionally moved, but the TONE pair may snapshot other live parameters; no volume-specific bitfield claimed",
            "A ramp and stationary hold do not guarantee identical values at every step; no uniform maximum pattern is predicted",
            "Compare lockB against actual plain-playbackA; preserve all differences, auxiliary changes and previously empty cells",
            "No volume writer or pitch-field writer is enabled; software never counts as hardware verification",
        ],
    }
    for directory, leg in zip(directories, registration["expected_capture_sequence"]):
        directory.mkdir()
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_plain_playback_or_tone_lock_probe",
                    "expected_file": "capture.wav",
                    "registration": "../sound3-tone-lock-probe-registration-001.json",
                    "planned_actions": [
                        "Keep Pattern1/Sound3/TONE, tempo100 and swing9; knobA untouched",
                        leg["action"],
                        "Save complete stereo backup at established reduced levels with one second trailing silence before the next action",
                        "After B report whether Sound3 became louder and any display value seen; leave Sound3/TONE stopped/write off",
                    ],
                }
            ),
        )
    write_bytes(registration_path, json_bytes(registration))
    print(
        json.dumps(
            {
                "registered": True,
                "capture_ids": CAPTURE_IDS,
                "volume_field": "unknown",
                "maximum_display": "unknown",
            }
        )
    )


if __name__ == "__main__":
    main()
