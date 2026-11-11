"""Register the FX period test: loop lengths of FX 1, 2, 3, 4 and 12 at 60 BPM.

The direction test read FX 1 and 2 as loops of about 250 and 333 ms of the sample's start
and FX 3, 4 and 12 as shorter loops or retriggers (docs/fx-direction-results.md). This
test measures each repetition period from a pitch track over 1.2 s of a held note on the
four-segment sample.

Source: the verified FX direction state. Patterns 1..5 play Sound6 key 1 on steps 1 and 5
with FX 1, 2, 3, 4 and 12 held on steps 5..16, so the second note is under the effect
for 3 s; Pattern 6 is the control. Chain 1..6, tempo 60.

Models of the period, registered before the session, as fractions of a 4 s bar: 1/8, 1/12,
1/16, 1/24, 1/32, 1/48 and 1/64 (500, 333, 250, 167, 125, 83 and 62.5 ms). Each effect is
classified as the candidate within 8% of the measured period, or unresolved; the control
note must have no period.
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
from scripts.fx_period_method import SETTINGS
from scripts.prepare_fx_direction_test import DIRECTORY as SOURCE_EXPERIMENT

HELD = {1: 1, 2: 2, 3: 3, 4: 4, 5: 12}
CONTROL_PATTERN = 6
CHAIN = [1, 2, 3, 4, 5, 6]
NOTE_STEPS = [1, 5]
HOLD_STEPS = list(range(5, 17))
TEMPO = 60
BAR_MS = 4 * 60000 / TEMPO
CANDIDATES = {f"1/{d}": BAR_MS / d for d in (8, 12, 16, 24, 32, 48, 64)}
TOLERANCE = 0.08
PLAN_DIRECTORY = "fx-period-plan-001"
DIRECTORY = "compiled-fx-period-001"
REGISTRATION = "fx-period-registration-001.json"
PLAYBACK_SECONDS = 28
QUESTION = "Did the looping effects sound faster from one pattern to the next? (Enter to skip)"


def effects_for(pattern):
    fx = HELD.get(pattern)
    return [fx if fx and step in HOLD_STEPS else None for step in range(1, 17)]


def keys():
    return [1 if step in NOTE_STEPS else None for step in range(1, 17)]


def classify(period):
    if period is None:
        return "unresolved"
    fits = [name for name, ms in CANDIDATES.items() if abs(period - ms) <= TOLERANCE * ms]
    return fits[0] if len(fits) == 1 else "unresolved"


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
        raise ValueError("The verified FX direction state is required")
    source = decode_artifact(load_artifact(source_path))
    parameters = {"pitch": 13, "volume": 36, "filter": 63, "resonance": 1}
    operations = []
    for pattern in CHAIN:
        operations.append(
            {
                "operation": "set_notes",
                "pattern": pattern,
                "sound": 6,
                "keys": keys(),
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
        if melodic_notes(target, pattern, 6) != keys() or step_effects(
            target, pattern
        ) != effects_for(pattern):
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
                "analysis_version": "fx-period-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "held_effects": {str(k): v for k, v in HELD.items()},
                "note_steps": NOTE_STEPS,
                "hold_steps": HOLD_STEPS,
                "control_pattern": CONTROL_PATTERN,
                "chain": CHAIN,
                "candidates_ms": CANDIDATES,
                "tolerance": TOLERANCE,
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/fx_period_method.py"),
                "descriptor_method_script_sha256": sha256_file(
                    root / "scripts/fx_descriptor_method.py"
                ),
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "The control's held-position note has no period",
                    "Each effect is classified as the single candidate within 8% of its measured period, else unresolved",
                ],
                "limits": [
                    "One tempo; whether the periods scale with tempo is not tested",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "candidates_ms": CANDIDATES}))


if __name__ == "__main__":
    main()
