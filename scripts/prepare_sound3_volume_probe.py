"""Register selection-only and minimum TONE volume captures without guessing a field."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact

CAPTURE_IDS = ("event-041-a-sound3-tone-selected", "event-042-b-sound3-tone-volume-minimum")


def main():
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    registration_path = root / "experiments/sound3-tone-volume-probe-registration-001.json"
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh registration and both capture directories required")
    baseline = root / "experiments/edited-joint-tempo100-swing9-001"
    observation_path = baseline / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    artifact_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not observation["joint_tempo_swing_composition_verified"]
        or not all(observation["checks"].values())
        or sha256_file(artifact_path) != observation["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Verified unchanged joint100/swing9 baseline required")
    frame = decode_artifact(load_artifact(artifact_path))
    if frame.packets[2].payload[129:131] != bytes([100, 9]):
        raise ValueError("Expected current100 BPM and swing9")
    registration = {
        "analysis_version": "sound3-selection-and-minimum-tone-volume-preregistration-0.1",
        "registered_before_all_captures": True,
        "hardware_verified": False,
        "baseline_artifact": artifact_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": observation["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_capture_sha256": observation["capture_sha256"],
        "baseline_body_sha256": observation["body_sha256"],
        "baseline_observation_sha256": sha256_file(observation_path),
        "expected_tempo_bpm": 100,
        "expected_swing_byte": 9,
        "expected_capture_sequence": [
            {
                "experiment_id": CAPTURE_IDS[0],
                "action": "Select Sound3/TONE without moving knobs; no playback or note audition before capture",
                "expected_body_sha256": None,
            },
            {
                "experiment_id": CAPTURE_IDS[1],
                "action": "Sound3/TONE stopped/write off; turn only B fully counterclockwise without holding BPM or another button; capture before any audition",
                "expected_body_sha256": None,
            },
        ],
        "location_hypotheses": {
            "selection_only_no_serialized_change": "Compare complete selectionA body to currentSound8 baseline",
            "volume_no_serialized_change": "A valid possible outcome: live TONE settings may be transient or omitted from the backup",
            "volume_changes_only_non_sample_non_pattern_packets": "Preserve sample records and all patterns; report every other changed tag, index and payload offset",
            "volume_changes_pattern_parameters": "Alternative retained and reported despite write-off instruction; no event bytes guessed",
            "minimum_display_and_raw_value_unknown": True,
        },
        "manual_observations_requested": [
            "Report actual display label/number while adjusting B if visible; do not infer it from bytes",
            "After saving B tap Sound3 keyboard key1 with write off and report silent,quieter or unchanged",
            "No original volume number or return setting is guessed",
        ],
        "official_control_reference": "https://teenage.engineering/guides/po-33/en#section6",
        "limits": [
            "No candidate volume offset, numeric scale, minimum display or predicted body supplied",
            "SelectionA is a fresh control; B is compared against actualA, never only against priorSound8",
            "No volume writer enabled, and an unchanged backup is retained as a meaningful outcome",
            "Only software/capture evidence is generated automatically; later user observations remain separate",
        ],
    }
    for directory, leg in zip(directories, registration["expected_capture_sequence"]):
        directory.mkdir()
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_sound3_selection_or_volume_probe",
                    "expected_file": "capture.wav",
                    "registration": "../sound3-tone-volume-probe-registration-001.json",
                    "planned_actions": [
                        "Keep Pattern1, stopped/write off, tempo100 and swing9; knobA untouched",
                        leg["action"],
                        "Save complete stereo capture.wav at established reduced levels with one second trailing silence before next action",
                        "After B has been saved, audition Sound3 key1 and report sound/display observations; leave Sound3/TONE stopped/write off",
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
                "minimum_display": "unknown",
            }
        )
    )


if __name__ == "__main__":
    main()
