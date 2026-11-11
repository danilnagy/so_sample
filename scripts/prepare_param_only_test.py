"""Register the parameter-only lock test: does a lock on an empty step set the held value?

The device stores locks on steps without a note as parameter-only cells (primary bytes
with a zero auxiliary byte). Code 0 on a note keeps the last locked value
(docs/no-lock-results.md). This test asks which locks count.

Source: the verified no-lock state (Sound16 sawtooth kit). Through the public plan path,
the chain becomes 1, 2:
- Pattern1: Sound16 notes on odd steps with filter NOTE_FILTERS (0 = unlocked) and
  resonance 1; parameter-only filter locks on even steps from PARAM_FILTERS.
- Pattern2: Sound16 notes on odd steps with filter REFERENCE_FILTERS, all locked, as
  references for each value.

Models of the four unlocked Pattern1 notes (steps 3, 5, 9 and 13):
- param_only_sets_value: each plays at the parameter-only lock just before it:
  24, 50, 20 and 24.
- param_only_ignored: each plays at the last locked note value: 63, 63, 63 and 56.
A model holds when every unlocked note is within 1.5 dB of the matching Pattern2
reference (median over harmonics at -30 dB or more, median over cycles).
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain
from po33_re.formats.notes import step_parameters
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.filter_response_method import SETTINGS
from scripts.prepare_no_lock_test import DIRECTORY as SOURCE_EXPERIMENT

CHAIN = [1, 2]
ODD = [1 if step % 2 else None for step in range(1, 17)]
NOTE_FILTERS = [63, None, 0, None, 0, None, 63, None, 0, None, 56, None, 0, None, 63, None]
PARAM_FILTERS = [None, 24, None, 50, None, None, None, 20, None, None, None, 24] + [None] * 4
REFERENCE_FILTERS = [63, None, 24, None, 50, None, 63, None, 20, None, 56, None, 24, None, 63, None]
UNLOCKED_STEPS = [3, 5, 9, 13]
MODELS = {"param_only_sets_value": [24, 50, 20, 24], "param_only_ignored": [63, 63, 63, 56]}
PLAN_DIRECTORY = "param-only-plan-001"
DIRECTORY = "compiled-param-only-001"
REGISTRATION = "param-only-registration-001.json"
PLAYBACK_SECONDS = 44
CYCLES = 5
TOLERANCE_DB, FLOOR_DB = 1.5, -30.0
QUESTION = "Did two patterns of eight buzzy notes alternate? (Enter to skip)"


def reference_step(value):
    """The Pattern2 step locked to this filter value."""
    return REFERENCE_FILTERS.index(value) + 1


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
        or not observation["checks"]["session_target_exact"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified no-lock state is required")
    source = decode_artifact(load_artifact(source_path))
    operations = []
    for p, filters in ((1, NOTE_FILTERS), (2, REFERENCE_FILTERS)):
        # Uniform parameters first: the note writer copies one identical parameter set.
        operations += [
            {
                "operation": "set_step_parameters",
                "pattern": p,
                "sound": 16,
                "parameter": name,
                "values": [value] * 16,
            }
            for name, value in (("filter", 16), ("resonance", 1))
        ]
        operations += [
            {
                "operation": "set_drum_notes",
                "pattern": p,
                "sound": 16,
                "keys": ODD,
                "template_sound": 16,
            },
            {
                "operation": "set_step_parameters",
                "pattern": p,
                "sound": 16,
                "parameter": "filter",
                "values": filters,
            },
            {
                "operation": "set_step_parameters",
                "pattern": p,
                "sound": 16,
                "parameter": "resonance",
                "values": [1 if k else None for k in ODD],
            },
        ]
    operations.append(
        {
            "operation": "set_parameter_locks",
            "pattern": 1,
            "sound": 16,
            "parameter": "filter",
            "values": PARAM_FILTERS,
        }
    )
    operations.append({"operation": "set_pattern_chain", "patterns": CHAIN})
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
    data = pattern_data(target, 1)
    param_cells = [
        data[48 * (s - 1) + 45 : 48 * (s - 1) + 48].hex()
        for s, v in enumerate(PARAM_FILTERS, 1)
        if v is not None
    ]
    if (
        drum_notes(target, 1, 16) != ODD
        or drum_notes(target, 2, 16) != ODD
        or [None if s is None else s["filter"] for s in step_parameters(target, 1, 16)][::2]
        != NOTE_FILTERS[::2]
        or len(param_cells) != 4
        or pattern_chain(target) != CHAIN
    ):
        raise ValueError("Compiled target does not hold the planned cells")
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
                "analysis_version": "param-only-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "note_filters": NOTE_FILTERS,
                "param_only_filters": PARAM_FILTERS,
                "param_only_cells_hex": param_cells,
                "reference_filters": REFERENCE_FILTERS,
                "unlocked_steps": UNLOCKED_STEPS,
                "models": MODELS,
                "tolerance_db": TOLERANCE_DB,
                "floor_db": FLOOR_DB,
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/filter_response_method.py"),
                "cycles_measured": CYCLES,
                "limits": [
                    "Filter locks only, on one drum sound; parameter-only cells for other parameters are not played",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "param_only_cells": param_cells}))


if __name__ == "__main__":
    main()
