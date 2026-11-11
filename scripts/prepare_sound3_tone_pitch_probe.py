"""Register a recorded TONE A probe after verified ordinary-playback persistence."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.formats.volume import calibrated_sound3_volumes
from po33_re.modem.symbols import load_artifact

CAPTURE_ID = "event-051-b-sound3-tone-pitch-lock-down"
REGISTRATION = "sound3-tone-pitch-down-registration-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    source_folder = root / "experiments/event-050-a-sound3-volume36-post-playback"
    observation_path = source_folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(source_folder / "capture.wav") != observation["capture_sha256"]
        or calibrated_sound3_volumes(decode_artifact(load_artifact(source_path))) != (36,) * 16
    ):
        raise ValueError("Verified exact post-playback uniform36 baseline required")
    directory = root / "experiments" / CAPTURE_ID
    registration_path = root / "experiments" / REGISTRATION
    if directory.exists() or directory.is_symlink() or registration_path.exists():
        raise ValueError("Fresh pitch probe directory and registration required")
    directory.mkdir()
    limits = [
        "First primary low6 bits are a new location hypothesis, not a decoded pitch field",
        "No endpoint raw code, semitone scale, numeric UI reading or complete target body is guessed",
        "Recorded A may snapshot volume or other TONE data even with B untouched; compare strict and broader alternatives separately",
        "Movement may retain a per-step ramp; the stationary hold does not guarantee uniform endpoint data",
        "Auxiliary changes, other sounds, sample data, globals and other patterns remain explicit; no decoder repair or silent mask widening",
        "No pitch-field writer or new extension of the public volume context; out-of-context volume edits continue to fail",
    ]
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "sound3-recorded-tone-A-down-preregistration-0.1",
                "registered_before_capture": True,
                "hardware_verified": False,
                "experiment_id": CAPTURE_ID,
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
                "recorded_action": {
                    "mode": "TONE",
                    "sound": 3,
                    "pattern": 1,
                    "moving_knob": "A",
                    "direction": "counterclockwise_to_physical_minimum",
                    "ramp_seconds": 5,
                    "stationary_write_hold_seconds": 3,
                    "knob_B_moved": False,
                },
                "location_hypotheses": {
                    "no_serialized_change": "Complete body stays equal to actual post-playback baseline",
                    "strict_pitch_candidate_only": "At least one Sound3 first-primary low6 field changes; only first-byte mask0x3f changes across all16 Sound3/P1 cells, auxiliary and all other state exact",
                    "pitch_candidate_plus_known_volume": "At least one first-low6 field changes; first-byte0xff and second-byte0x0f only, auxiliary and all other state exact",
                    "other_sound3_primary_changes": "Only Sound3/P1 primary cells change, with auxiliary exact; full raw tuples retained without field interpretation",
                    "sound3_primary_and_auxiliary_changes": "Only Sound3/P1 primary and auxiliary cells change; full raw tuples and auxiliary values retained",
                },
                "expected_audition_direction": "Sound3 should drop in pitch during counterclockwise movement; independent user report may be unknown",
                "display_text_required": False,
                "raw_endpoint_value_assumed": None,
                "official_control_source": "https://teenage.engineering/guides/po-33/en",
                "limits": limits,
            }
        ),
    )
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": CAPTURE_ID,
                "capture_status": "awaiting_recorded_TONE_A_down_capture",
                "registration": "../" + REGISTRATION,
                "planned_actions": [
                    "Select Pattern1/Sound3/TONE with playback stopped and write off; keep B and all audio settings unchanged",
                    "Start Pattern1, hold WRITE and slowly move only A counterclockwise to its physical minimum over about5 seconds",
                    "Continue holding WRITE for3 seconds with both knobs stationary; do not press keyboard keys or hold BPM/FX",
                    "Release WRITE, stop playback and ensure write off; record full capture.wav at established reduced level with one second trailing silence",
                    "Report whether Sound3 dropped in pitch and any display text actually observed; uncertain or absent readings remain unknown; leave A at minimum and B untouched",
                ],
            }
        ),
    )
    write_bytes(
        directory / "instructions.md",
        b"# Recorded Sound 3 TONE pitch down\n\nSelect Pattern 1 / Sound 3 / TONE, stopped and write off. Keep B and all\naudio settings unchanged. Start Pattern 1, hold WRITE, and slowly turn only\nA fully counterclockwise over about 5 seconds. Hold WRITE for another\n3 seconds with both knobs stationary. Release WRITE, stop playback and\nensure write off. Do not press keyboard keys or hold BPM/FX during the pass.\n\nSave a full backup here as capture.wav at the established reduced level,\nwith one second trailing silence. Report whether Sound 3 dropped in pitch\nand any display text actually seen; uncertainty is acceptable. Leave A at\nminimum and B untouched. No restore or separate playback recording is needed.\n",
    )
    print(
        json.dumps(
            {
                "registered": True,
                "experiment": CAPTURE_ID,
                "source_body_sha256": observation["body_sha256"],
                "hardware_verified": False,
            }
        )
    )


if __name__ == "__main__":
    main()
