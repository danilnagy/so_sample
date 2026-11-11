"""Register the stray bits observation: auxiliary high nibbles and global bytes 131..146.

Two fields still have no measured meaning. The auxiliary byte's high nibble has only ever
been F (melodic note) or 1 (drum note). Bytes 131..146 of the second global record, one
per pattern, changed after playback stops and were called a per-pattern stop step.

Source: the verified project-build state. Through the public plan path, chain [2], tempo
100 kept, swing 0, and Pattern2 rewritten: Sound8 (C5 tone) key 1 on every odd step with
pitch 13, plus raw cells on even steps and raw global bytes:

  step 2: Sound8 primary normal, auxiliary 0x20 (nibble 2, key 1)
  step 4: Sound8 auxiliary 0x10 (the drum nibble on a melodic sound)
  step 6: Sound13 (300 Hz) auxiliary 0xF0 (the melodic nibble on a drum sound)
  step 8: Sound8 auxiliary 0xE0 (nibble E, key 1)
  step 10: Sound8 auxiliary 0x00 with nonzero primary: a parameter-only cell, control
  step 12: Sound8 auxiliary 0xF5 (melodic key 6) with the pitch field 0: pitch is unlocked
  global bytes 131..146 = 1..16

Reception outcomes are recorded per cell and per global byte: kept, rewritten, or
cleared. Playback: for each even step, whether Sound8's or Sound13's tone sounds in the
step and at what frequency, read exploratively; the registered hypotheses are:
- raw_values_kept: the backup equals the target exactly.
- odd_steps_normal: every odd step sounds Sound8 at 784 Hz.
No prediction is made for the even steps; their readings are the observation.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.polyphony_method_exploratory import SETTINGS as LEVEL_BASE
from scripts.prepare_project_build_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_project_build_test import MELODY_KEY1_HZ

PATTERN = 2
NORMAL = "0df907"  # pitch 13, volume 36, filter 63, resonance 1
NO_PITCH = "00f907"  # pitch 0 (unlocked), same other fields
RAW_CELLS = {
    2: (8, NORMAL, 0x20),
    4: (8, NORMAL, 0x10),
    6: (13, NORMAL, 0xF0),
    8: (8, NORMAL, 0xE0),
    10: (8, NORMAL, 0x00),
    12: (8, NO_PITCH, 0xF5),
}
GLOBAL_BYTES = {131 + k: k + 1 for k in range(16)}
ODD_STEPS = list(range(1, 17, 2))
STEP_SECONDS = 60 / 100 / 4
VOICES = {
    "sound8_key1": MELODY_KEY1_HZ,
    "sound8_key6": MELODY_KEY1_HZ * 2 ** (-5 / 12),
    "sound13": 300.0,
}
LEVEL_SETTINGS = {**LEVEL_BASE, "step_seconds": STEP_SECONDS, "window_ms": [60.0, 140.0]}
PLAN_DIRECTORY = "stray-bits-plan-001"
DIRECTORY = "compiled-stray-bits-001"
REGISTRATION = "stray-bits-registration-001.json"
PLAYBACK_SECONDS = 22
QUESTION = "Did any of the in-between steps play a note, and did the screen show anything odd? (Enter to skip)"


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
        or observation["classification"] != "project_plays_as_built"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified project-build state is required")
    source = decode_artifact(load_artifact(source_path))
    parameters = {"pitch": 13, "volume": 36, "filter": 63, "resonance": 1}
    operations = [
        {
            "operation": "set_notes",
            "pattern": PATTERN,
            "sound": sound,
            "keys": [None] * 16,
            "parameters": parameters,
        }
        for sound in range(1, 17)
    ]
    operations.append(
        {
            "operation": "set_notes",
            "pattern": PATTERN,
            "sound": 8,
            "keys": [1 if s in ODD_STEPS else None for s in range(1, 17)],
            "parameters": parameters,
        }
    )
    operations.append({"operation": "set_step_effects", "pattern": PATTERN, "effects": [None] * 16})
    operations += [
        {
            "operation": "set_raw_cell",
            "pattern": PATTERN,
            "step": step,
            "sound": sound,
            "primary_hex": primary,
            "auxiliary": auxiliary,
        }
        for step, (sound, primary, auxiliary) in RAW_CELLS.items()
    ]
    operations += [
        {"operation": "set_global_byte", "ordinal": 1, "offset": offset, "value": value}
        for offset, value in GLOBAL_BYTES.items()
    ]
    operations += [
        {"operation": "set_swing_byte", "value": 0},
        {"operation": "set_pattern_chain", "patterns": [PATTERN]},
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
    data = pattern_data(target, PATTERN)
    for step, (sound, primary, auxiliary) in RAW_CELLS.items():
        p, a = 48 * (step - 1) + 3 * (sound - 1), 768 + 16 * (step - 1) + sound - 1
        if data[p : p + 3].hex() != primary or data[a] != auxiliary:
            raise ValueError(f"Raw cell at step {step} is not as planned")
    second = [p.payload for p in target.packets if p.tag == 0x7D5C][1]
    if any(second[o] != v for o, v in GLOBAL_BYTES.items()) or pattern_chain(target) != [PATTERN]:
        raise ValueError("Global bytes or chain are not as planned")
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
                "analysis_version": "stray-bits-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "raw_cells": {str(k): [s, p, a] for k, (s, p, a) in RAW_CELLS.items()},
                "global_bytes": {str(k): v for k, v in GLOBAL_BYTES.items()},
                "odd_steps": ODD_STEPS,
                "voices_hz": VOICES,
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "level_settings": LEVEL_SETTINGS,
                "level_method_script_sha256": sha256_file(
                    root / "scripts/polyphony_method_exploratory.py"
                ),
                "hypotheses": {
                    "raw_values_kept": "the backup equals the target exactly",
                    "odd_steps_normal": "every odd step sounds Sound8 key 1 within 10 dB of step 1",
                },
                "decision": [
                    "Reception is classified per raw cell and per global byte: kept, rewritten or cleared",
                    "Even steps are read exploratively: level of each voice against step 1's Sound8 level",
                ],
                "limits": [
                    "One pattern; six raw cells and sixteen global bytes; no model for the even steps",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
