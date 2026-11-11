"""Register a hardware test of the public set_melodic_notes edit-plan operation.

From the verified keyboard-scale state (Sound3 key s on step s, 60 BPM, no effects), a
hash-bound plan rewrites Pattern 1's Sound3 notes to a shuffled melody that uses every
key once. The restore is compiled through the public apply-edits path. The frozen
grid-only method measures every step, and the confirmed row layout predicts each step's
interval from step 1. The previous state's order is registered as the alternative.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_key_scale_grid_method import SETTINGS
from scripts.prepare_pattern1_key_scale_map_rerun import ROW_LAYOUT

SOURCE_EXPERIMENT = "edited-pattern1-key-scale-map-002"
PLAN_DIRECTORY = "melodic-notes-plan-001"
DIRECTORY = "compiled-melodic-notes-writer-001"
REGISTRATION = "melodic-notes-writer-registration-001.json"
MELODY = [16, 1, 15, 2, 14, 3, 13, 4, 12, 5, 11, 6, 10, 7, 9, 8]
PLAYBACK_SECONDS = 22
QUESTION = "Did the melody jump between low and high notes? (Enter to skip)"


def cents_relative_to_step1(keys):
    return [ROW_LAYOUT[k - 1] - ROW_LAYOUT[keys[0] - 1] for k in keys]


MODELS = {
    "melody_written": cents_relative_to_step1(MELODY),
    "previous_order_kept": cents_relative_to_step1(list(range(1, 17))),
}


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    plan_folder = root / "experiments" / PLAN_DIRECTORY
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if plan_folder.exists() or folder.exists() or registration_path.exists():
        raise ValueError("Fresh plan folder, output folder and registration required")
    source_folder = root / "experiments" / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified keyboard-scale state is required")
    source_frame = decode_artifact(load_artifact(source_path))
    if melodic_notes(source_frame, 1, 3) != list(range(1, 17)):
        raise ValueError("Source must hold Sound3 key s on step s")
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(source_path),
        "source_body_sha256": hashlib.sha256(source_frame.encoded_body).hexdigest(),
        "operations": [
            {"operation": "set_melodic_notes", "pattern": 1, "sound": 3, "keys": MELODY}
        ],
    }
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    report = compile_edit_plan(source_path, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    if melodic_notes(target, 1, 3) != MELODY:
        raise ValueError("Compiled target does not hold the planned melody")
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../" + REGISTRATION,
                "plan": "../" + PLAN_DIRECTORY + "/plan.json",
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
                "analysis_version": "melodic-notes-writer-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "plan": plan_path.relative_to(root).as_posix(),
                "plan_sha256": sha256_file(plan_path),
                "compile_report_sha256": sha256_file(folder / "compile-report.json"),
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": plan["source_artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "melody_keys": MELODY,
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "decision": [
                    "The backup must equal the compiled target exactly; only Pattern 1's Sound3 auxiliary bytes may differ from the source",
                    "Pitches are measured with the frozen grid-only method; cents are relative to step 1",
                    "A model holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                ],
                "limits": [
                    "Sound3 on Pattern 1 with one shared set of note parameters",
                    "Other melodic sounds are expected to share the key layout but were not measured",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "melody": MELODY}))


if __name__ == "__main__":
    main()
