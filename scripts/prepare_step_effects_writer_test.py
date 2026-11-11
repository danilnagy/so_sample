"""Register a hardware test of the public set_step_effects edit-plan operation.

Starting from the verified 16-note, 60 BPM state (full step map -001 backup), a
hash-bound plan sets Pattern 1's effects to FX key 7 (octave up) on steps 1, 4, 7, 8,
9, 12, 15 and 16, the complement of the earlier layout. The restore is compiled by the
public apply-edits path. The frozen per-note-gate method then classifies all 16 notes on
fresh recordings: the sequential, high-nibble-first layout predicts exactly those steps.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_fx_note_gate_method import SETTINGS
from scripts.prepare_pattern1_fx_full_step_map import nibble_steps
from scripts.prepare_pattern1_fx_full_step_map_confirm import METHOD_FILES

SOURCE_EXPERIMENT = "edited-pattern1-FX-full-step-map-001"
PLAN_DIRECTORY = "step-effects-plan-001"
DIRECTORY = "compiled-step-effects-writer-001"
REGISTRATION = "step-effects-writer-registration-001.json"
EFFECT_STEPS = (1, 4, 7, 8, 9, 12, 15, 16)
FX_KEY = 7
PLAYBACK_SECONDS = 22
QUESTION = "Roughly which notes sounded higher, if you could tell? (Enter to skip)"


def effects_list():
    return [FX_KEY if step in EFFECT_STEPS else None for step in range(1, 17)]


def predictions(footer):
    return {
        "sequential_high_nibble_first": {
            str(s): ("effect" if s in nibble_steps(footer, True) else "none") for s in range(1, 17)
        },
        "sequential_low_nibble_first": {
            str(s): ("effect" if s in nibble_steps(footer, False) else "none") for s in range(1, 17)
        },
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
    if not observation["checks"]["native_check_passed"]:
        raise ValueError("The 16-note state must have been received exactly")
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if sha256_file(source_path) != native["artifact_sha256"]:
        raise ValueError("Source artifact changed")
    source_frame = decode_artifact(load_artifact(source_path))
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(source_path),
        "source_body_sha256": hashlib.sha256(source_frame.encoded_body).hexdigest(),
        "operations": [{"operation": "set_step_effects", "pattern": 1, "effects": effects_list()}],
    }
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    report = compile_edit_plan(source_path, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    footer = pattern_data(target, 1)[1024:]
    source_data, target_data = pattern_data(source_frame, 1), pattern_data(target, 1)
    if nibble_steps(footer, True) != list(EFFECT_STEPS):
        raise ValueError("Compiled footer does not place the effect on the planned steps")
    if source_data[:1024] != target_data[:1024]:
        raise ValueError("Pattern 1 notes changed")
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
                "analysis_version": "step-effects-writer-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "plan": (plan_folder / "plan.json").relative_to(root).as_posix(),
                "plan_sha256": sha256_file(plan_path),
                "compile_report_sha256": sha256_file(folder / "compile-report.json"),
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": plan["source_artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "footer": footer.hex(),
                "effect_steps": list(EFFECT_STEPS),
                "fx_key": FX_KEY,
                "reference_frequency_hz": json.loads(
                    (
                        root / "experiments/pattern1-single-tone-FX-order-registration-001.json"
                    ).read_text()
                )["reference_frequency_hz"],
                "method_settings": SETTINGS,
                **{key: sha256_file(root / path) for key, path in METHOD_FILES.items()},
                "predictions": predictions(footer),
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "Only Pattern 1's footer may differ from the 16-note source state",
                    "Each of the 16 notes is classified with the frozen per-note-gate method",
                    "A model holds only if all 16 steps match in their five-loop median and at least 4 of 5 loops",
                ],
                "limits": [
                    "Tests the writer with FX key 7 on Pattern 1; other keys rely on the device code map",
                    "The stored effect codes of other keys are verified; their sound is not measured",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "footer": footer.hex()}))


if __name__ == "__main__":
    main()
