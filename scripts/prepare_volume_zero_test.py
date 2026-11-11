"""Register the volume-code-0 test and a reproduction of the measured gain table.

In the volume law run, code 0 played at the preceding step's level (volume 36) within
0.002 dB. This plan alternates measured codes with 0, so each 0 follows a different level:
63, 0, 9, 0, 36, 0, 21, 0, 54, 0, 3, 0, 45, 0, 27, 0. Registered before the recording:

- table_reproduced: every nonzero step within 0.5 dB of the first run's gain table
- hold_previous: every 0 step within 0.5 dB of its preceding step
- fixed_default: all 0 steps within 0.5 dB of one another
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.notes import step_parameters
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact
from scripts.check_volume_law_test import DECISION as FIRST_DECISION
from scripts.pattern1_volume_gain_method import SETTINGS

SOURCE_EXPERIMENT = "compiled-volume-law-001"
PLAN_DIRECTORY = "volume-zero-plan-001"
DIRECTORY = "compiled-volume-zero-001"
REGISTRATION = "volume-zero-registration-001.json"
VOLUME_CODES = [63, 0, 9, 0, 36, 0, 21, 0, 54, 0, 3, 0, 45, 0, 27, 0]
TOLERANCE_DB = 0.5
PLAYBACK_SECONDS = 22
QUESTION = "Did the notes alternate between changing and steady levels? (Enter to skip)"


def predicted_nonzero_db(table):
    """dB relative to step 1 for each nonzero step, from the first run's gain table."""
    reference = table[str(VOLUME_CODES[0])]
    return [None if code == 0 else table[str(code)] - reference for code in VOLUME_CODES]


def decide_zero(levels_by_step, predicted, tolerance=TOLERANCE_DB):
    """levels_by_step: step -> median dB relative to step 1."""
    reproduced = all(
        levels_by_step[step] is not None
        and abs(levels_by_step[step] - predicted[step - 1]) <= tolerance
        for step in range(1, 17)
        if predicted[step - 1] is not None
    )
    zero_steps = [step for step in range(1, 17) if VOLUME_CODES[step - 1] == 0]
    zero_levels = [levels_by_step[step] for step in zero_steps]
    hold = all(
        levels_by_step[step] is not None
        and abs(levels_by_step[step] - levels_by_step[step - 1]) <= tolerance
        for step in zero_steps
    )
    fixed = None not in zero_levels and max(zero_levels) - min(zero_levels) <= tolerance
    models = {"hold_previous": hold, "fixed_default": fixed}
    supported = [name for name, ok in models.items() if ok]
    classification = supported[0] if reproduced and len(supported) == 1 else "other_or_inconclusive"
    return {
        "table_reproduced": reproduced,
        "model_support": models,
        "classification": classification,
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
        raise ValueError("The verified volume-law state is required")
    first_decision = json.loads((root / "experiments" / FIRST_DECISION).read_text())
    table = first_decision["measured_db_by_code"]
    predicted = predicted_nonzero_db(table)
    source_frame = decode_artifact(load_artifact(source_path))
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(source_path),
        "source_body_sha256": hashlib.sha256(source_frame.encoded_body).hexdigest(),
        "operations": [
            {
                "operation": "set_step_parameters",
                "pattern": 1,
                "sound": 3,
                "parameter": "volume",
                "values": VOLUME_CODES,
            }
        ],
    }
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    report = compile_edit_plan(source_path, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    if [p["volume"] for p in step_parameters(target, 1, 3)] != VOLUME_CODES:
        raise ValueError("Compiled target does not hold the planned volume codes")
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
                "analysis_version": "volume-zero-registration-0.1",
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
                "volume_codes": VOLUME_CODES,
                "first_run_table_db_vs_36": table,
                "first_run_decision_sha256": sha256_file(root / "experiments" / FIRST_DECISION),
                "predicted_nonzero_db_vs_step1": predicted,
                "tolerance_db": TOLERANCE_DB,
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_volume_gain_method.py"
                ),
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "Levels are measured with the frozen volume method (RMS 50-90 ms, median of five loops, dB vs step 1)",
                    "table_reproduced: every nonzero step within 0.5 dB of the first run's table",
                    "hold_previous: every 0 step within 0.5 dB of the step before it; fixed_default: all 0 steps within 0.5 dB of one another",
                    "A model is supported only if the table also reproduces and exactly one model holds",
                ],
                "limits": [
                    "Sound3 at pitch 13 on Pattern 1",
                    "Does not test what a 0 step does after a rest or at the start of playback",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "predicted": predicted}))


if __name__ == "__main__":
    main()
