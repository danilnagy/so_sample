"""Register a backup of the device as it stands after the audition-lock sessions.

The device holds the audition-lock restore; since then Pattern 1 has played several
times, Sound 16 was selected, and knob B was turned fully clockwise with WRITE off, which
made the sound audible by hand. This backup, taken without a restore, is compared byte
for byte with the registered target to see whether any of that was stored.

Outcomes, by where bytes differ from the target, as in the knob observation:
- nothing_stored: the backup equals the target.
- global_records_only: only 0x7d5c record bytes differ.
- sound16_cells_only: only Pattern cells of Sound 16 differ.
- sound_records_only: only sample or reference records differ.
- mixed: differences in more than one of these regions.

Prediction, registered before the backup: nothing_stored, from the knob observation,
where turning Sound 16's knobs without WRITE stored nothing.
"""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from scripts.prepare_audition_lock_observation import DIRECTORY as SOURCE
from scripts.prepare_audition_lock_observation import REGISTRATION as SOURCE_REGISTRATION

DIRECTORY = "observe-audition-knob-dump-001"
REGISTRATION = "audition-knob-dump-registration-001.json"
OUTCOMES = [
    "nothing_stored",
    "global_records_only",
    "sound16_cells_only",
    "sound_records_only",
    "mixed",
]
PREDICTION = "nothing_stored"
QUESTIONS = [
    "Since the retakes, did you touch anything on the device besides knob B, PLAY and key 1? (Enter to skip)",
]
INSTRUCTIONS = """Back up the device as it is now. Do not restore first and do not touch the knobs.
Keep WRITE off and playback stopped, then press WRITE + SOUND + PLAY when the recording is armed."""


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    folder = experiments / DIRECTORY
    registration_path = experiments / REGISTRATION
    if folder.exists() or registration_path.exists():
        raise ValueError("Fresh folder and registration required")
    source_registration = json.loads((experiments / SOURCE_REGISTRATION).read_text())
    target = experiments / SOURCE / "edited.symbols.npz"
    if sha256_file(target) != source_registration["edited_artifact_sha256"]:
        raise ValueError("The registered target changed")
    folder.mkdir()
    write_bytes(folder / "instructions.md", INSTRUCTIONS.encode())
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "kind": "device_side_observation_without_restore",
                "capture_status": "awaiting_hardware_session",
                "expected_artifact": "../" + SOURCE + "/edited.symbols.npz",
                "source_artifact": "../" + SOURCE + "/edited.symbols.npz",
                "restore_of_record": "../" + SOURCE + "/restore.wav",
                "registration": "../" + REGISTRATION,
                "playback_seconds": 0,
                "observation_questions": QUESTIONS,
                "hardware_restore": {"status": "none; the device holds the audition-lock restore"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "audition-knob-dump-registration-0.1",
                "hardware_verified": False,
                "registered_before_backup": True,
                "experiment_id": DIRECTORY,
                "target_artifact": target.relative_to(root).as_posix(),
                "target_artifact_sha256": sha256_file(target),
                "restore_of_record_sha256": source_registration["restore_wav_sha256"],
                "device_actions_since_restore": [
                    "Pattern 1 played several times",
                    "Sound 16 selected (SOUND + key 16)",
                    "knob B turned fully clockwise with WRITE off",
                    "key 1 pressed by hand many times",
                ],
                "instructions": INSTRUCTIONS,
                "outcomes": OUTCOMES,
                "prediction": PREDICTION,
                "prediction_basis": "docs/sound-knobs-results.md: knobs turned without WRITE stored nothing",
                "limits": [
                    "One device; the actions since the restore are as the person reports them"
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
