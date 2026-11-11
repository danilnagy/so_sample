"""Register the keyboard scale map rerun with a grid-only method and a fourth model.

The first run was received exactly but played back at 80 BPM after an accidental tempo
change, so its registered decision was inconclusive. Its exploratory 80 BPM reading
suggested a row layout on the 4x4 key grid; that layout is registered here as a fourth
model next to chromatic, major and natural minor, before fresh recordings. The restore
files are the first run's, checked byte for byte. Keep the BPM untouched this time.
"""

import argparse
import json
import shutil
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from scripts.pattern1_key_scale_grid_method import SETTINGS
from scripts.pattern1_key_scale_method import MODELS as FIRST_MODELS
from scripts.prepare_pattern1_key_scale_map import DIRECTORY as FIRST_DIRECTORY
from scripts.prepare_pattern1_key_scale_map import QUESTION
from scripts.prepare_pattern1_key_scale_map import REGISTRATION as FIRST_REGISTRATION

DIRECTORY = "edited-pattern1-key-scale-map-002"
REGISTRATION = "pattern1-key-scale-map-rerun-registration-001.json"
PLAYBACK_SECONDS = 22
ROW_LAYOUT = [
    0,
    100,
    300,
    400,
    -700,
    -500,
    -400,
    -200,
    -1200,
    -1100,
    -900,
    -800,
    -1900,
    -1700,
    -1600,
    -1400,
]
MODELS = {**FIRST_MODELS, "row_layout_from_first_run": ROW_LAYOUT}
COPIED = ("edited.symbols.npz", "restore.wav", "redecoded.symbols.npz", "software-validation.json")


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if folder.exists() or registration_path.exists():
        raise ValueError("Fresh folder and registration required")
    first_path = root / "experiments" / FIRST_REGISTRATION
    first = json.loads(first_path.read_text())
    first_folder = root / "experiments" / FIRST_DIRECTORY
    if (
        sha256_file(first_folder / "edited.symbols.npz") != first["edited_artifact_sha256"]
        or sha256_file(first_folder / "restore.wav") != first["restore_wav_sha256"]
    ):
        raise ValueError("The first run's registered restore files changed")
    folder.mkdir()
    for name in COPIED:
        shutil.copyfile(first_folder / name, folder / name)
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../" + REGISTRATION,
                "restore_copied_from": "../" + FIRST_DIRECTORY,
                "playback_seconds": PLAYBACK_SECONDS,
                "observation_questions": [QUESTION],
                "hardware_restore": {"status": "not_run"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "key-scale-map-rerun-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "first_registration_sha256": sha256_file(first_path),
                "first_observation_sha256": sha256_file(
                    first_folder / "hardware-observation-001.json"
                ),
                "source_artifact": first["source_artifact"],
                "source_artifact_sha256": first["source_artifact_sha256"],
                "source_capture_sha256": first["source_capture_sha256"],
                "first_capture_sha256": json.loads(
                    (first_folder / "hardware-recapture-results-001.json").read_text()
                )["capture_sha256"],
                "expected_body_sha256": first["expected_body_sha256"],
                "edited_artifact_sha256": first["edited_artifact_sha256"],
                "restore_wav_sha256": first["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "row_layout_source": "exploratory 80 BPM reading of the first run's playback",
                "decision": [
                    "The backup must equal the target exactly",
                    "Pitches are measured on the 250 ms step grid from the first note's onset, 5-40 ms after each step",
                    "A model holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                    "Otherwise other_or_inconclusive; the measured table is reported either way",
                ],
                "limits": first["limits"],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
