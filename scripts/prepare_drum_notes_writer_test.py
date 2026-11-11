"""Register the drum-notes writer test: Sound11 keys 1..16 on steps 1..16 of Pattern1.

Source: the device's own backup after recording 16 tone bursts into drum Sound11. Slice k
holds burst k at 400 * 2^((k-1)/8) Hz, so successive slices are 150 cents apart.

Through the public plan path: Sound11 key k on step k, written as auxiliary byte
0x10 + k - 1 with the parameters of Sound3's notes (pitch code 13, volume 36); then the
Sound3 and Sound7 notes in Pattern1 are cleared so Sound11 plays alone. Keys 1 and 2 have
been recorded on the device before; keys 3..16 are new values.

Models of the per-step pitch, in cents relative to step 1:
- key_k_plays_slice_k: 150 * (k - 1)
- every_key_plays_slice_1: 0 on every step

Secondary, the absolute pitch of step 1 against the 400 Hz first burst:
- stored_rate: 0 cents (drums play their recording unchanged at pitch code 13)
- plus_7_semitones: +700 cents (the fixed offset melodic sounds show at key 1)
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes, melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_key_scale_grid_method import SETTINGS as GRID_SETTINGS
from scripts.prepare_drum11_record_observation import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_drum11_record_observation import FREQUENCIES

PLAN_DIRECTORY = "drum-notes-plan-001"
DIRECTORY = "compiled-drum-notes-001"
REGISTRATION = "drum-notes-registration-001.json"
SETTINGS = {**GRID_SETTINGS, "window_starts_ms": [15.0, 25.0, 35.0]}
DRUM_KEYS = list(range(1, 17))
EMPTY = [None] * 16
PLAYBACK_SECONDS = 22
QUESTION = "Did the pattern play a rising run of 16 short beeps? (Enter to skip)"
MODELS = {
    "key_k_plays_slice_k": [150.0 * (k - 1) for k in DRUM_KEYS],
    "every_key_plays_slice_1": [0.0] * 16,
}
ABSOLUTE_MODELS = {"stored_rate": 0.0, "plus_7_semitones": 700.0}


def absolute_decision(step1_hz):
    if step1_hz is None:
        return {"step1_cents_vs_burst1": None, "classification": "other_or_inconclusive"}
    cents = 1200 * math.log2(step1_hz / FREQUENCIES[0])
    close = [
        name
        for name, value in ABSOLUTE_MODELS.items()
        if abs(cents - value) <= SETTINGS["cents_tolerance"]
    ]
    return {
        "step1_cents_vs_burst1": cents,
        "classification": close[0] if len(close) == 1 else "other_or_inconclusive",
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    plan_folder = root / "experiments" / PLAN_DIRECTORY
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if registration_path.exists() or plan_folder.exists() or folder.exists():
        raise ValueError("Fresh folders and registration required")
    source_folder = root / "experiments" / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or not observation["slices_1_to_15_hold_bursts_1_to_15_in_order"]
    ):
        raise ValueError("The recorded drum Sound11 state is required")
    source = decode_artifact(load_artifact(source_path))
    if drum_notes(source, 1, 11) != EMPTY:
        raise ValueError("Sound11 must have no notes in Pattern1")
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(source_path),
        "source_body_sha256": hashlib.sha256(source.encoded_body).hexdigest(),
        "operations": [
            {"operation": "set_step_effects", "pattern": 1, "effects": EMPTY},
            {
                "operation": "set_drum_notes",
                "pattern": 1,
                "sound": 11,
                "keys": DRUM_KEYS,
                "template_sound": 3,
            },
            {"operation": "set_melodic_notes", "pattern": 1, "sound": 3, "keys": EMPTY},
            {"operation": "set_melodic_notes", "pattern": 1, "sound": 7, "keys": EMPTY},
        ],
    }
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    report = compile_edit_plan(source_path, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    if (
        drum_notes(target, 1, 11) != DRUM_KEYS
        or melodic_notes(target, 1, 3) != EMPTY
        or melodic_notes(target, 1, 7) != EMPTY
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
                "analysis_version": "drum-notes-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": plan["source_artifact_sha256"],
                "source_capture_sha256": sha256_file(source_folder / "capture.wav"),
                "burst_frequencies_hz": FREQUENCIES,
                "plan_sha256": sha256_file(plan_path),
                "compile_report_sha256": sha256_file(folder / "compile-report.json"),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "absolute_models_cents_vs_burst1": ABSOLUTE_MODELS,
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "Pitches are measured with the frozen grid method 15-55 ms after each grid onset; cents relative to step 1",
                    "A model holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                    "Secondary: the step 1 median is compared with the 400 Hz first burst; a model holds within 20 cents",
                ],
                "limits": [
                    "One drum sound (Sound11) holding one device recording; other drum slots follow by the same layout but are not played here",
                    "All notes share one parameter set at pitch code 13; drum pitch and other parameters are not varied",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}, indent=2))


if __name__ == "__main__":
    main()
