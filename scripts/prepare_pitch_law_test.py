"""Register a per-step pitch-code law test through the public plan path.

From the verified melody state, a hash-bound plan sets every Sound3 note in Pattern 1 to
key 1 (set_melodic_notes) and then gives each step its own pitch code
(set_step_parameters). Only codes 13 and 14 have been measured, about one semitone apart.
The registered model is one semitone per code across the observed range 1..25; the
alternative is that the per-step codes are ignored and every note keeps one pitch.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.notes import step_parameters
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_key_scale_grid_method import SETTINGS

SOURCE_EXPERIMENT = "compiled-melodic-notes-writer-001"
PLAN_DIRECTORY = "pitch-law-plan-001"
DIRECTORY = "compiled-pitch-law-001"
REGISTRATION = "pitch-law-registration-001.json"
PITCH_CODES = [13, 1, 25, 7, 19, 4, 22, 10, 16, 2, 24, 5, 21, 8, 18, 12]
PLAYBACK_SECONDS = 22
QUESTION = "Did the notes jump around in pitch? (Enter to skip)"
MODELS = {
    "semitone_per_code": [100 * (code - PITCH_CODES[0]) for code in PITCH_CODES],
    "codes_ignored": [0] * 16,
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
        raise ValueError("The verified melody state is required")
    source_frame = decode_artifact(load_artifact(source_path))
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(source_path),
        "source_body_sha256": hashlib.sha256(source_frame.encoded_body).hexdigest(),
        "operations": [
            {"operation": "set_melodic_notes", "pattern": 1, "sound": 3, "keys": [1] * 16},
            {
                "operation": "set_step_parameters",
                "pattern": 1,
                "sound": 3,
                "parameter": "pitch",
                "values": PITCH_CODES,
            },
        ],
    }
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    report = compile_edit_plan(source_path, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    parameters = step_parameters(target, 1, 3)
    if melodic_notes(target, 1, 3) != [1] * 16 or [p["pitch"] for p in parameters] != PITCH_CODES:
        raise ValueError("Compiled target does not hold the planned keys and pitch codes")
    before = step_parameters(source_frame, 1, 3)
    for old, new in zip(before, parameters):
        if {k: v for k, v in old.items() if k != "pitch"} != {
            k: v for k, v in new.items() if k != "pitch"
        }:
            raise ValueError("A field other than pitch changed")
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
                "analysis_version": "pitch-law-registration-0.1",
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
                "pitch_codes": PITCH_CODES,
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "decision": [
                    "The backup must equal the compiled target exactly; only Pattern 1's Sound3 cells may differ",
                    "Pitches are measured with the frozen grid-only method; cents are relative to step 1 (code 13)",
                    "A model holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                    "Otherwise inconclusive; the measured table is reported either way",
                ],
                "limits": [
                    "Sound3 with key 1 on Pattern 1; codes outside 1..25 are not tested",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "codes": PITCH_CODES}))


if __name__ == "__main__":
    main()
