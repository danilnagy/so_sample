"""Register a fresh backup and playback of the full step map, judged by the per-note gate.

The first run (-001) was received exactly, but its registered result was inconclusive:
fully engaged octave notes fell below the recording-peak audibility gate. The amended
method (pattern1_fx_note_gate_method.py) gates each note on its own peak; it was
developed on the -001 playback, which is therefore not evidence here. The device still
holds the -001 state, so this run takes a new backup (which must equal the same target)
and a new playback, without a restore.
"""

import argparse
import json
import shutil
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from scripts.pattern1_fx_note_gate_method import SETTINGS
from scripts.prepare_pattern1_fx_full_step_map import DIRECTORY as FIRST_DIRECTORY
from scripts.prepare_pattern1_fx_full_step_map import PREDICTIONS, QUESTION
from scripts.prepare_pattern1_fx_full_step_map import REGISTRATION as FIRST_REGISTRATION

DIRECTORY = "edited-pattern1-FX-full-step-map-002"
REGISTRATION = "pattern1-FX-full-step-map-confirm-registration-001.json"
PLAYBACK_SECONDS = 22
METHOD_FILES = {
    "note_gate_script_sha256": "scripts/pattern1_fx_note_gate_method.py",
    "grid_script_sha256": "scripts/pattern1_fx_grid_pitch_method.py",
    "grouping_script_sha256": "scripts/pattern1_fx_multi_step_pitch_method.py",
    "step1_script_sha256": "scripts/pattern1_fx_step_pitch_method.py",
}


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
    observation = json.loads((first_folder / "hardware-observation-001.json").read_text())
    if not observation["hardware_verified"] or not observation["checks"]["native_check_passed"]:
        raise ValueError("The -001 state must have been received exactly")
    target = first_folder / "edited.symbols.npz"
    if sha256_file(target) != first["edited_artifact_sha256"]:
        raise ValueError("The registered -001 target changed")
    folder.mkdir()
    shutil.copyfile(target, folder / "edited.symbols.npz")
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_hardware_session",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../" + REGISTRATION,
                "device_state_from": "../" + FIRST_DIRECTORY,
                "playback_seconds": PLAYBACK_SECONDS,
                "observation_questions": [QUESTION],
                "hardware_restore": {"status": "not_applicable_state_already_on_device"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "FX-full-step-map-confirm-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_backup_and_playback": True,
                "experiment_id": DIRECTORY,
                "first_registration_sha256": sha256_file(first_path),
                "first_observation_sha256": sha256_file(
                    first_folder / "hardware-observation-001.json"
                ),
                "method_developed_on": FIRST_DIRECTORY + "/playback.wav",
                "source_artifact": first["source_artifact"],
                "source_artifact_sha256": first["source_artifact_sha256"],
                "source_capture_sha256": first["source_capture_sha256"],
                "expected_body_sha256": first["expected_body_sha256"],
                "edited_artifact_sha256": first["edited_artifact_sha256"],
                "first_capture_sha256": json.loads(
                    (first_folder / "hardware-recapture-results-001.json").read_text()
                )["capture_sha256"],
                "footer": first["footer"],
                "reference_frequency_hz": first["reference_frequency_hz"],
                "method_settings": SETTINGS,
                **{key: sha256_file(root / path) for key, path in METHOD_FILES.items()},
                "predictions": PREDICTIONS,
                "decision": [
                    "The new backup must equal the registered target exactly",
                    "Each of the 16 notes is classified 20-130 ms after its grid onset with the frozen thresholds, gating windows at 20% of that note's own peak",
                    "A model holds only if all 16 steps are found and each matches in its five-loop median and at least 4 of 5 loops",
                    "Anything else is inconclusive; the observed per-step map is reported either way",
                ],
                "limits": first["limits"],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
