"""Register the drum pitch test: does the pitch code transpose a drum note?

Source: the verified chain-writer state. Sound16's key-1 window holds a 272 ms, 800 Hz
tone (sample-memory test kit). Through the public plan path:
1. Sound16 key 1 on every step of Pattern1, with Sound1's note parameters (pitch 13).
2. set_step_parameters gives each step a pitch code from PITCH_CODES.
3. The melodic notes of Sound1..8 in Pattern1 are cleared, and the chain is set to [1].

Models of the per-step pitch relative to step 1 (frozen grid method, 20 ms windows 50,
60 and 70 ms after each grid onset, past the melodic glide):
- semitone_per_code: 100 (code - 13) cents, as for melodic sounds.
- no_transposition: 0 cents on every step.
Absolute: step 1 (code 13) within 20 cents of 800 Hz, the stored rate.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.drum_import import drum_windows
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain
from po33_re.formats.notes import step_parameters
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes
from po33_re.modem.symbols import load_artifact
from scripts.prepare_chain_writer_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_pitch_law_confirm import SETTINGS

PITCH_CODES = [13, 15, 17, 19, 21, 23, 25, 11, 9, 7, 5, 3, 1, 14, 12, 13]
BASE_HZ = 800.0
PLAN_DIRECTORY = "drum-pitch-plan-001"
DIRECTORY = "compiled-drum-pitch-001"
REGISTRATION = "drum-pitch-registration-001.json"
PLAYBACK_SECONDS = 22
QUESTION = "Did one drum sound play at changing pitches? (Enter to skip)"
MODELS = {
    "semitone_per_code": [100.0 * (code - 13) for code in PITCH_CODES],
    "no_transposition": [0.0] * 16,
}


def absolute_decision(step1_hz):
    if step1_hz is None:
        return {"step1_cents_vs_stored": None, "stored_rate": False}
    cents = 1200 * math.log2(step1_hz / BASE_HZ)
    return {
        "step1_cents_vs_stored": cents,
        "stored_rate": abs(cents) <= SETTINGS["cents_tolerance"],
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
        or observation["classification"] != "chain_5_1_1"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified chain-writer state is required")
    source = decode_artifact(load_artifact(source_path))
    if drum_windows(source, 16)[0] != (0, 6375, 120):
        raise ValueError("Sound16 key 1 must hold the 6375-code memory-test tone")
    operations = [
        {
            "operation": "set_drum_notes",
            "pattern": 1,
            "sound": 16,
            "keys": [1] * 16,
            "template_sound": 1,
        },
        {
            "operation": "set_step_parameters",
            "pattern": 1,
            "sound": 16,
            "parameter": "pitch",
            "values": PITCH_CODES,
        },
        *(
            {"operation": "set_melodic_notes", "pattern": 1, "sound": s, "keys": [None] * 16}
            for s in range(1, 9)
        ),
        {"operation": "set_pattern_chain", "patterns": [1]},
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
        drum_notes(target, 1, 16) != [1] * 16
        or [p["pitch"] for p in step_parameters(target, 1, 16)] != PITCH_CODES
        or pattern_chain(target) != [1]
    ):
        raise ValueError("Compiled target does not hold the planned notes")
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
                "analysis_version": "drum-pitch-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "pitch_codes": PITCH_CODES,
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "absolute_hz": BASE_HZ,
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "A model holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                    "Absolute: step 1 within 20 cents of 800 Hz",
                ],
                "limits": [
                    "One drum sound, key 1, volume 36; pitch codes 1..25 sampled at 13 values",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
