"""Register the loop length test: FX 1, 2 and 15 held over fifteen steps of a key run.

FX 14 looped four steps from the pattern start and FX 11 and 12 repeated one step; FX 1,
2 and 15 changed nothing when held on steps 5..12 (docs/fx-pattern-results.md). If they are
loops of 8, 12 and 16 steps, holding them over steps 2..16 must show replays for any loop
shorter than the pattern.

Source: the verified FX pattern state. Patterns 1..5 play Sound8 keys 1..16 with FX 1, 2,
15, 14 and 11 held on steps 2..16; Pattern 6 is the control. Chain 1..6, tempo 60, one
cycle of 24 s.

Models of the key heard on step s (2..16) for each held effect, registered before the
session, with the pattern-start loop seen for FX 14 as the template:
- loop_N: key = ((s - 1) mod N) + 1 for N in 1, 4, 8, 12, 16 (16 is the identity).
Each held effect is classified as the single N that matches every step at 100 ms, or
unresolved. FX 14 should read loop_4 and FX 11 loop_1.
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
from scripts.prepare_fx_pattern_observation import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_fx_pattern_observation import KEY_HZ, RUN, TEMPO

HELD = {1: 1, 2: 2, 3: 15, 4: 14, 5: 11}
CONTROL_PATTERN = 6
CHAIN = [1, 2, 3, 4, 5, 6]
HOLD_STEPS = list(range(2, 17))
LOOP_LENGTHS = [1, 4, 8, 12, 16]
PLAN_DIRECTORY = "fx-loop-plan-001"
DIRECTORY = "compiled-fx-loop-001"
REGISTRATION = "fx-loop-registration-001.json"
PLAYBACK_SECONDS = 28
QUESTION = "Did any pattern sound like it kept repeating its opening notes? (Enter to skip)"


def loop_prediction(length):
    return [((s - 1) % length) + 1 for s in range(1, 17)]


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
        raise ValueError("The verified FX pattern state is required")
    source = decode_artifact(load_artifact(source_path))
    # Patterns 1..16 already hold the key run on Sound8; only the effects and chain change.
    operations = [
        {"operation": "set_step_effects", "pattern": pattern, "effects": effects_for(pattern)}
        for pattern in CHAIN
    ]
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
                "analysis_version": "fx-loop-registration-0.1",
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
                "key_hz": KEY_HZ,
                "loop_predictions": {str(n): loop_prediction(n) for n in LOOP_LENGTHS},
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/fx_pattern_method.py"),
                "descriptor_method_script_sha256": sha256_file(
                    root / "scripts/fx_descriptor_method.py"
                ),
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "The control pattern plays key k on step k within 20 cents at 100 ms",
                    "Each held effect is classified as the one loop length whose prediction matches the key at 100 ms on every step 2..16, else unresolved",
                ],
                "limits": [
                    "Loop lengths 1, 4, 8, 12 and 16 only; other behaviours are reported as unresolved",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
