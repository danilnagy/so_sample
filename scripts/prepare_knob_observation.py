"""Register a device-side observation: turn the knobs on Sound16 without WRITE.

Code 0 in a step's filter, resonance or volume means no parameter lock: the step keeps
the last locked value (docs/no-lock-results.md). The first unlocked step in a recording
played at a value no lock had set, so a sound-level setting exists. Earlier knob tests
held WRITE, which records locks into the pattern. This observation turns the knobs
without WRITE to find where, if anywhere, the sound-level setting is stored.

The verified no-lock restore is played first, so the device starts from a known state.

Outcomes registered before the backup, by where the bytes that differ from the restored
target lie:
- nothing_stored: the backup equals the restored target.
- global_records_only: only 0x7d5c record bytes differ.
- sound16_cells_only: only Pattern cells (primary or auxiliary bytes) of Sound16 differ.
- sound_records_only: only sample or reference records differ.
- mixed: differences in more than one of these regions.
"""

import argparse
import json
import shutil
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from scripts.prepare_no_lock_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_no_lock_test import REGISTRATION as SOURCE_REGISTRATION

DIRECTORY = "observe-sound-knobs-001"
REGISTRATION = "sound-knobs-registration-001.json"
OUTCOMES = [
    "nothing_stored",
    "global_records_only",
    "sound16_cells_only",
    "sound_records_only",
    "mixed",
]
QUESTIONS = [
    "Which parameter names did the screen show for knobs A and B, and which way did you turn each? (Enter to skip)",
    "Anything else you noticed? (Enter to skip)",
]
INSTRUCTIONS = """Change Sound 16's knob settings without recording them into the pattern:

1. Keep playback stopped and WRITE off.
2. Select Sound 16 (hold SOUND and press key 16).
3. Turn knob A fully counterclockwise, then knob B fully clockwise.
4. Note the parameter names the screen shows while you turn them.

Do not press WRITE, play or any pattern key before the backup."""


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    folder = experiments / DIRECTORY
    registration_path = experiments / REGISTRATION
    if folder.exists() or registration_path.exists():
        raise ValueError("Fresh folder and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    if not observation["hardware_verified"] or not observation["checks"]["session_target_exact"]:
        raise ValueError("The verified no-lock state is required")
    source_registration = json.loads((experiments / SOURCE_REGISTRATION).read_text())
    restore = source_folder / "restore.wav"
    target = source_folder / "edited.symbols.npz"
    if (
        sha256_file(restore) != source_registration["restore_wav_sha256"]
        or sha256_file(target) != source_registration["edited_artifact_sha256"]
    ):
        raise ValueError("The verified restore or its target changed")
    folder.mkdir()
    shutil.copyfile(restore, folder / "restore.wav")
    write_bytes(folder / "instructions.md", INSTRUCTIONS.encode())
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "kind": "device_side_observation_after_restore",
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "source_artifact": "../" + SOURCE_EXPERIMENT + "/edited.symbols.npz",
                "registration": "../" + REGISTRATION,
                "playback_seconds": 0,
                "observation_questions": QUESTIONS,
                "hardware_restore": {"status": "not_run"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "sound-knobs-registration-0.1",
                "hardware_verified": False,
                "registered_before_backup": True,
                "experiment_id": DIRECTORY,
                "restore_wav_sha256": sha256_file(folder / "restore.wav"),
                "baseline_artifact": target.relative_to(root).as_posix(),
                "baseline_artifact_sha256": sha256_file(target),
                "instructions": INSTRUCTIONS,
                "outcomes": OUTCOMES,
                "limits": [
                    "One sound and one knob movement each way; the knob pages and value scales are reported, not controlled",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
