"""Register the FX onsets observation at 120 BPM: timing of FX 9, 10, 12 and 13 on a run.

At 60 BPM FX 9 cut notes short, FX 10 gated the third and fourth of every four steps, FX 12
retriggered every 250 ms and FX 13 echoed the note from two steps earlier
(docs/fx-pattern-results.md, docs/fx-period-120-results.md). This observation measures their
onset timing at 120 BPM on a run of sixteen keys, to see which of them follow the tempo.

Source: the verified tempo-sync state. Patterns 1..4 play Sound8's C5 tone with keys 1..16
on every step and FX 9, 10, 12 and 13 held on steps 5..12; Pattern 5 is the control.
Chain 1..5, tempo 120, so a step lasts 125 ms and a cycle 10 s.

Registered before the session: the backup equals the target exactly, and the control run
plays key k on step k with one onset per step. Each held step's onsets, their times within
the step and the key heard 50 ms in are described, not predicted.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.effects import step_effects
from po33_re.formats.globals import pattern_chain, swing, tempo
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.fx_pattern_method import SETTINGS as BASE_SETTINGS
from scripts.prepare_fx_pattern_observation import KEY_HZ, RUN
from scripts.prepare_fx_period_120_test import DIRECTORY as SOURCE_EXPERIMENT

HELD = {1: 9, 2: 10, 3: 12, 4: 13}
CONTROL_PATTERN = 5
CHAIN = [1, 2, 3, 4, 5]
HOLD_STEPS = list(range(5, 13))
TEMPO = 120
STEP_SECONDS = 60 / TEMPO / 4
SETTINGS = {**BASE_SETTINGS, "step_seconds": STEP_SECONDS, "window_starts_ms": [50.0, 90.0]}
PLAN_DIRECTORY = "fx-onsets-120-plan-001"
DIRECTORY = "compiled-fx-onsets-120-001"
REGISTRATION = "fx-onsets-120-registration-001.json"
PLAYBACK_SECONDS = 24
CYCLES = 2
QUESTION = "Did the gated and stuttered patterns sound twice as fast as at 60 BPM? (Enter to skip)"


def effects_for(pattern):
    fx = HELD.get(pattern)
    return [fx if fx and step in HOLD_STEPS else None for step in range(1, 17)]


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
        or not observation["hypotheses"]["exact_reception"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified tempo-sync state is required")
    source = decode_artifact(load_artifact(source_path))
    parameters = {"pitch": 13, "volume": 36, "filter": 63, "resonance": 1}
    operations = []
    for pattern in CHAIN:
        operations += [
            {
                "operation": "set_notes",
                "pattern": pattern,
                "sound": sound,
                "keys": [None] * 16,
                "parameters": parameters,
            }
            for sound in range(1, 17)
            if sound != 8
        ]
        operations.append(
            {
                "operation": "set_notes",
                "pattern": pattern,
                "sound": 8,
                "keys": RUN,
                "parameters": parameters,
            }
        )
        operations.append(
            {"operation": "set_step_effects", "pattern": pattern, "effects": effects_for(pattern)}
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
    for pattern in CHAIN:
        if melodic_notes(target, pattern, 8) != RUN or step_effects(target, pattern) != effects_for(
            pattern
        ):
            raise ValueError(f"Pattern{pattern} is not as planned")
    if pattern_chain(target) != CHAIN or tempo(target) != TEMPO or swing(target) != 0:
        raise ValueError("Globals are not as planned")
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
                "analysis_version": "fx-onsets-120-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "held_effects": {str(k): v for k, v in HELD.items()},
                "hold_steps": HOLD_STEPS,
                "control_pattern": CONTROL_PATTERN,
                "chain": CHAIN,
                "tempo": TEMPO,
                "key_hz": KEY_HZ,
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/fx_pattern_method.py"),
                "descriptor_method_script_sha256": sha256_file(
                    root / "scripts/fx_descriptor_method.py"
                ),
                "cycles_measured": CYCLES,
                "hypotheses": {
                    "exact_reception": "the backup equals the target exactly",
                    "control_run": "the control pattern plays key k on step k within 20 cents at 50 ms, one onset per step",
                },
                "limits": [
                    "One tempo, 120 BPM, compared with the 60 BPM run; one melodic tone",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
