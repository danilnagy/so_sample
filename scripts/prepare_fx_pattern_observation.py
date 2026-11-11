"""Register the FX pattern observation: each effect over a run of sixteen different pitches.

Six effects left a single note untouched (docs/fx-catalog-results.md), so they must act on
the pattern. Here Patterns 1..15 each play Sound8 (C5 tone) on every step with keys 1..16
in order, sixteen distinct pitches, and effect k on steps 5..12 of Pattern k. Pattern 16 is
the same run with no effect, the control. Chain 1..16; tempo 60; swing 0. One cycle lasts
64 s and the playback records one cycle.

Registered before the session: the backup equals the target exactly, and the control
pattern plays key k on step k within 20 cents at 100 ms, one onset per step. Every other
pattern is described, not predicted: which pitch sounds at each step, at what level, and
how many onsets the step has.
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
from scripts.fx_pattern_method import SETTINGS
from scripts.prepare_fx_catalog_observation import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_project_build_test import MELODY_KEY1_HZ

KEY_SEMITONES = [0, 1, 3, 4, -7, -5, -4, -2, -12, -11, -9, -8, -19, -17, -16, -14]
KEY_HZ = [MELODY_KEY1_HZ * 2 ** (s / 12) for s in KEY_SEMITONES]
RUN = list(range(1, 17))
FX_STEPS = list(range(5, 13))
CONTROL_PATTERN = 16
CHAIN = list(range(1, 17))
TEMPO = 60
PLAN_DIRECTORY = "fx-pattern-plan-001"
DIRECTORY = "compiled-fx-pattern-001"
REGISTRATION = "fx-pattern-registration-001.json"
PLAYBACK_SECONDS = 70
QUESTION = "Which effects clearly changed the run of notes, and how? (Enter to skip)"


def effects_for(pattern):
    if pattern == CONTROL_PATTERN:
        return [None] * 16
    return [pattern if step in FX_STEPS else None for step in range(1, 17)]


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
        raise ValueError("The verified FX catalogue state is required")
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
    operations += [
        {"operation": "set_tempo_byte", "bpm": TEMPO},
        {"operation": "set_swing_byte", "value": 0},
        {"operation": "set_pattern_chain", "patterns": CHAIN},
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
                "analysis_version": "fx-pattern-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "key_hz": KEY_HZ,
                "fx_steps": FX_STEPS,
                "control_pattern": CONTROL_PATTERN,
                "chain": CHAIN,
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/fx_pattern_method.py"),
                "descriptor_method_script_sha256": sha256_file(
                    root / "scripts/fx_descriptor_method.py"
                ),
                "hypotheses": {
                    "exact_reception": "the backup equals the target exactly",
                    "control_run": "the control pattern plays key k on step k within 20 cents at 100 ms, one onset per step",
                },
                "limits": [
                    "One cycle at tempo 60 with one melodic tone; effects are described in this setting only",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
