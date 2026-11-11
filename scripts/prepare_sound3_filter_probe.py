"""Register FILTER selection and an A-only recorded pass with competing bit masks."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.formats.pitch import calibrated_sound3_pitches
from po33_re.modem.symbols import load_artifact

CAPTURE_IDS = ("event-054-a-sound3-filter-selection", "event-055-b-sound3-filter-A-lock-up")
REGISTRATION = "sound3-filter-selection-and-A-registration-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    source_folder = root / "experiments/edited-sound3-pitch14-001"
    observation_path = source_folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(source_folder / "capture.wav") != observation["capture_sha256"]
        or calibrated_sound3_pitches(decode_artifact(load_artifact(source_path))) != (14,) * 16
    ):
        raise ValueError("Verified generated14 and independent interval evidence required")
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    registration_path = root / "experiments" / REGISTRATION
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh FILTER registration and both capture directories required")
    limits = [
        "SelectionA controls the combined already performed ordinary playback and FILTER selection without knob movement; any difference cannot be attributed to selection alone",
        "First verify actual A before asking for recorded B; B is compared with actual A even if selection prediction fails",
        "Second-primary high0xf0 and third-primary low0x03 form a new location hypothesis, not a decoded cutoff field or width",
        "A-only recording may snapshot other FILTER data despite B staying untouched; coupled third-byte and broader primary/auxiliary alternatives remain separate",
        "A is physically at minimum after prior tests, so only the later clockwise pass requests movement; no minimum cutoff is assumed from knob position",
        "No endpoint code, exact target body for B, Hz curve, resonance scale, UI reading or uniformity is predicted",
        "No public filter writer or extension of pitch/volume context; changes outside existing guards remain unsupported",
    ]
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "sound3-FILTER-selection-and-recorded-A-preregistration-0.1",
                "registered_before_both_captures": True,
                "hardware_verified": False,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (source_folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": observation["body_sha256"],
                "source_observation_sha256": sha256_file(observation_path),
                "prior_ordinary_playback_sha256": observation["playback_sha256"],
                "expected_tempo_bpm": 100,
                "expected_swing_byte": 9,
                "expected_packet_count": 815,
                "expected_frame_end_byte": 156758,
                "expected_capture_sequence": [
                    {
                        "experiment_id": CAPTURE_IDS[0],
                        "action": "select_FILTER_stopped_write_off_both_knobs_untouched_after_existing_playback",
                        "expected_complete_body_sha256": observation["body_sha256"],
                    },
                    {
                        "experiment_id": CAPTURE_IDS[1],
                        "action": "later_record_only_A_clockwise_to_maximum_after_verifying_A",
                        "expected_endpoint_code": None,
                    },
                ],
                "candidate": {
                    "pattern": 1,
                    "sound": 3,
                    "second_primary_mask": 240,
                    "third_primary_mask": 3,
                },
                "broader_FILTER_candidate": {"second_primary_mask": 240, "third_primary_mask": 255},
                "location_hypotheses": [
                    "no_serialized_change",
                    "strict_candidate_mask_only",
                    "candidate_plus_other_third_byte_bits",
                    "other_Sound3_primary_changes",
                    "Sound3_primary_and_auxiliary_changes",
                ],
                "official_control_source": "https://teenage.engineering/guides/po-33/en",
                "limits": limits,
            }
        ),
    )
    for index, directory in enumerate(directories):
        directory.mkdir()
        actions = (
            [
                "Keep both knobs and audio settings unchanged; stop playback and ensure write off",
                "Select Pattern1/Sound3, press FX until FILTER selected without moving a knob",
                "Save complete capture.wav at established reduced recording level with one second trailing silence; no restore or extra playback needed",
                "Leave knobs untouched; recorded A adjustment waits for this capture to be verified",
            ]
            if index == 0
            else [
                "Wait for selectionA verification and further handoff before changing a knob",
                "Later use Pattern1/Sound3/FILTER, hold WRITE during playback and move only A clockwise to maximum over5 seconds; hold3 seconds stationary",
                "Keep B and audio settings untouched; release WRITE, stop and ensure write off before full capture.wav",
            ]
        )
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_FILTER_selection_without_knob_movement"
                    if index == 0
                    else "awaiting_verified_selection_before_recorded_FILTER_A",
                    "registration": "../" + REGISTRATION,
                    "planned_actions": actions,
                }
            ),
        )
    write_bytes(
        directories[0] / "instructions.md",
        b"# FILTER selection control\n\nKeep both knobs and all audio settings unchanged. Stop playback and ensure write\noff. Select Pattern 1 / Sound 3 and press FX until FILTER is selected, without\nturning either knob. Save a complete backup here as capture.wav at the established\nreduced recording level with one second trailing silence. No restore or separate\nplayback recording is needed. Confirm FILTER is selected and leave both knobs\nuntouched. The recorded A pass waits for this capture to be verified.\n",
    )
    print(
        json.dumps(
            {
                "registered": True,
                "next_capture": CAPTURE_IDS[0],
                "recorded_pass_pending": CAPTURE_IDS[1],
            }
        )
    )


if __name__ == "__main__":
    main()
