"""Register the FX catalogue observation: what each of the 15 effects does to a tone.

The effects footer and its code map are verified, but only FX 7's sound has been
characterised. A preview engine needs a description of every effect. This observation
plays Sound8's C5 tone (784 Hz, 200 ms at key 1) on odd steps with one effect per note:
Pattern2 holds FX 1..8 on steps 1, 3, ..., 15 and Pattern3 holds FX 9..15 on steps 1..13,
with step 15 effect-free as the control. Even steps are empty so a tail or repeat shows.
Chain 2, 3; tempo 60 (250 ms steps); swing 0.

Registered before the session: the backup equals the target exactly, and the control step
sounds like a plain note (one onset, 784 Hz, no energy in the following step). Every other
step is described, not predicted: onsets within the step pair, the dominant frequency in
40 ms windows, and the level in each window.
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
from scripts.prepare_project_build_test import MELODY_KEY1_HZ
from scripts.prepare_stray_bits_test import DIRECTORY as SOURCE_EXPERIMENT

CHAIN = [2, 3]
TEMPO = 60
STEP_SECONDS = 60 / TEMPO / 4
EFFECTS = {
    2: [
        k if s % 2 else None
        for s, k in zip(range(1, 17), [1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7, 0, 8, 0], strict=True)
    ],
    3: [
        k if s % 2 and k else None
        for s, k in zip(
            range(1, 17), [9, 0, 10, 0, 11, 0, 12, 0, 13, 0, 14, 0, 15, 0, 0, 0], strict=True
        )
    ],
}
NOTES = [1 if s % 2 else None for s in range(1, 17)]
CONTROL = (3, 15)
WINDOWS_MS = [
    (20, 60),
    (60, 100),
    (100, 140),
    (140, 180),
    (180, 220),
    (220, 260),
    (260, 300),
    (300, 340),
    (340, 380),
    (380, 420),
    (420, 460),
]
FX_OF_STEP = {
    (pattern, step): fx
    for pattern, effects in EFFECTS.items()
    for step, fx in enumerate(effects, 1)
    if fx
}
PLAN_DIRECTORY = "fx-catalog-plan-001"
DIRECTORY = "compiled-fx-catalog-001"
REGISTRATION = "fx-catalog-registration-001.json"
PLAYBACK_SECONDS = 26
CYCLES = 3
QUESTION = "Describe, in order, what each effect did to the note if you can (Enter to skip)"


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
        or not observation["hypotheses"]["raw_values_kept"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified stray-bits state is required")
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
        ]
        operations.append(
            {
                "operation": "set_notes",
                "pattern": pattern,
                "sound": 8,
                "keys": NOTES,
                "parameters": parameters,
            }
        )
        operations.append(
            {"operation": "set_step_effects", "pattern": pattern, "effects": EFFECTS[pattern]}
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
        if (
            melodic_notes(target, pattern, 8) != NOTES
            or step_effects(target, pattern) != EFFECTS[pattern]
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
                "analysis_version": "fx-catalog-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "effects": {str(k): v for k, v in EFFECTS.items()},
                "control_step": list(CONTROL),
                "tone_hz": MELODY_KEY1_HZ,
                "step_seconds": STEP_SECONDS,
                "windows_ms": WINDOWS_MS,
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_script_sha256": sha256_file(root / "scripts/fx_descriptor_method.py"),
                "hypotheses": {
                    "exact_reception": "the backup equals the target exactly",
                    "control_plain": "the control step has one onset, 784 Hz within 20 cents in every window where it sounds, and nothing above -30 dB in the following step",
                },
                "limits": [
                    "One tone, one key, tempo 60; effects that depend on tempo, key or sample content are described only in this setting",
                ],
            }
        ),
    )
    print(
        json.dumps(
            {
                "ready": True,
                "folder": DIRECTORY,
                "effects_per_step": {f"{p}:{s}": fx for (p, s), fx in FX_OF_STEP.items()},
            }
        )
    )


if __name__ == "__main__":
    main()
