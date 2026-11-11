"""Register the selected-pattern test: write Pattern5 and select it through global byte 0.

Source: the verified all-melodic-slots state. Pattern1 plays melodic Sound s on step
2s-1, a rising run of eight tones 150 cents apart; byte 0 of the second global record is 0.

Through the public plan path:
1. copy_pattern copies Pattern1 to Pattern5.
2. set_melodic_notes rewrites Pattern5 so Sound s plays on step 2(9-s)-1: the same eight
   tones falling.
3. set_selected_pattern sets byte 0 to 4, selecting Pattern5.

The person presses play without touching any pattern button. Models of the per-step pitch
relative to step 1 (frozen grid method):
- pattern5_selected: steps 2j-1 and 2j sound -150 (j-1) cents; step 1 is Sound8,
  within 20 cents of 733.6 * 2^(7/12) = 1099.1 Hz.
- pattern1_plays: steps 2j-1 and 2j sound +150 (j-1) cents; step 1 is Sound1 at 599.3 Hz.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import selected_pattern
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.prepare_all_melodic_slots_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_all_melodic_slots_test import SETTINGS, SLOTS, TONE_HZ, keys_for

PATTERN = 5
PLAN_DIRECTORY = "selected-pattern-plan-001"
DIRECTORY = "compiled-selected-pattern-001"
REGISTRATION = "selected-pattern-registration-001.json"
TRANSPOSE = 2 ** (7 / 12)
PLAYBACK_SECONDS = 22
QUESTION = "Did the pattern play eight falling notes? Did you need to press anything besides play? (Enter to skip)"
MODELS = {
    "pattern5_selected": [-150.0 * ((step - 1) // 2) for step in range(1, 17)],
    "pattern1_plays": [150.0 * ((step - 1) // 2) for step in range(1, 17)],
}
STEP1_HZ = {"pattern5_selected": TONE_HZ[8] * TRANSPOSE, "pattern1_plays": TONE_HZ[1] * TRANSPOSE}


def reversed_keys(slot):
    return keys_for(9 - slot)


def absolute_decision(step1_hz):
    if step1_hz is None:
        return {"cents_vs_models": None, "classification": "other_or_inconclusive"}
    cents = {name: 1200 * math.log2(step1_hz / hz) for name, hz in STEP1_HZ.items()}
    close = [name for name, c in cents.items() if abs(c) <= SETTINGS["cents_tolerance"]]
    return {
        "cents_vs_models": cents,
        "classification": close[0] if len(close) == 1 else "other_or_inconclusive",
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any(
        (experiments / name).exists() for name in (PLAN_DIRECTORY, DIRECTORY)
    ):
        raise ValueError("Fresh folders and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or observation["classification"] != "slot_s_plays_its_tone"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified all-melodic-slots state is required")
    source = decode_artifact(load_artifact(source_path))
    if selected_pattern(source) != 1 or any(
        melodic_notes(source, PATTERN, s) != [None] * 16 for s in SLOTS
    ):
        raise ValueError("Pattern1 must be selected and Pattern5 empty")
    operations = [
        {"operation": "copy_pattern", "source_pattern": 1, "destination_pattern": PATTERN},
        *(
            {
                "operation": "set_melodic_notes",
                "pattern": PATTERN,
                "sound": slot,
                "keys": reversed_keys(slot),
            }
            for slot in SLOTS
        ),
        {"operation": "set_selected_pattern", "pattern": PATTERN},
    ]
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(source_path),
        "source_body_sha256": hashlib.sha256(source.encoded_body).hexdigest(),
        "operations": operations,
    }
    plan_folder = experiments / PLAN_DIRECTORY
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    folder = experiments / DIRECTORY
    report = compile_edit_plan(source_path, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    if (
        selected_pattern(target) != PATTERN
        or any(melodic_notes(target, PATTERN, s) != reversed_keys(s) for s in SLOTS)
        or any(melodic_notes(target, 1, s) != keys_for(s) for s in SLOTS)
    ):
        raise ValueError("Compiled target does not hold the planned patterns")
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
                "analysis_version": "selected-pattern-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "step1_hz": STEP1_HZ,
                "decision": [
                    "The backup must equal the compiled target exactly, Pattern5 and global byte 0 included",
                    "A model holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                    "Absolute: step 1 within 20 cents of the model's step-1 frequency",
                ],
                "limits": [
                    "One pattern (5) selected by byte 0; other patterns and pattern chains are not tested",
                    "Playback starts with the play button only, right after the backup",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
