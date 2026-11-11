"""Register the FX rules test: FX 14's restart rule and FX 13's source note.

FX 14 held from step 5 replayed keys 1..4 over and over; held from step 2 it replayed key 1
(docs/fx-loop-results.md). FX 13 replaced the third of every four steps with a recent
note: the previous step's at 120 BPM, two steps earlier in one case at 60 BPM
(docs/fx-onsets-120-results.md). Source: the verified full-build state, where Sound8
holds a 0.3 s tone at 329.6 Hz (key 1 plays 493.9 Hz).

Patterns 1..5 play Sound8 keys 1..16 in order, sixteen distinct pitches, at tempo 60:
  Pattern1: FX 14 on steps 3..16    Pattern2: FX 14 on steps 7..16
  Pattern3: FX 14 on steps 9..16    Pattern4: FX 14 on steps 5..12
  Pattern5: FX 13 on steps 2..16    Pattern6: control
Chain 1..6, one cycle of 24 s.

Rules registered before the session, as the key heard 100 ms into each held step:
FX 14: loop_steps_before_hold, key = ((s-1) mod (start-1)) + 1; loop_power_of_two, the
same with the largest power of two not above start-1; restart_every_four, period 4.
FX 13: previous_on_third, the third step of each four plays the previous step's key;
two_earlier_on_third, it plays the key from two steps earlier; unchanged.
A rule holds for an effect when it matches every held step of every pattern using it.
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
from scripts.prepare_fx_pattern_observation import KEY_SEMITONES
from scripts.prepare_project_build_full_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_project_build_full_test import MELODIC_HZ

SOUND = 8
KEY1_HZ = MELODIC_HZ[SOUND] * 2 ** (7 / 12)
KEY_HZ = [KEY1_HZ * 2 ** (s / 12) for s in KEY_SEMITONES]
RUN = list(range(1, 17))
HOLDS = {1: (14, 3, 16), 2: (14, 7, 16), 3: (14, 9, 16), 4: (14, 5, 12), 5: (13, 2, 16)}
CONTROL_PATTERN = 6
CHAIN = [1, 2, 3, 4, 5, 6]
TEMPO = 60
SETTINGS = {**BASE_SETTINGS, "window_starts_ms": [30.0, 100.0, 180.0]}
PLAN_DIRECTORY = "fx-rules-plan-001"
DIRECTORY = "compiled-fx-rules-001"
REGISTRATION = "fx-rules-registration-001.json"
PLAYBACK_SECONDS = 28
QUESTION = "In the first four patterns, how many notes did each repeating loop seem to use? (Enter to skip)"


def effects_for(pattern):
    if pattern not in HOLDS:
        return [None] * 16
    fx, start, end = HOLDS[pattern]
    return [fx if start <= step <= end else None for step in range(1, 17)]


def power_of_two_at_most(n):
    p = 1
    while p * 2 <= n:
        p *= 2
    return p


def fx14_prediction(rule, start, step):
    if rule == "loop_steps_before_hold":
        n = start - 1
    elif rule == "loop_power_of_two":
        n = power_of_two_at_most(start - 1)
    elif rule == "restart_every_four":
        n = 4
    else:
        raise ValueError(rule)
    return ((step - 1) % n) + 1


def fx13_prediction(rule, step):
    third = (step - 1) % 4 == 2
    if rule == "previous_on_third":
        return step - 1 if third else step
    if rule == "two_earlier_on_third":
        return step - 2 if third else step
    if rule == "unchanged":
        return step
    raise ValueError(rule)


FX14_RULES = ["loop_steps_before_hold", "loop_power_of_two", "restart_every_four"]
FX13_RULES = ["previous_on_third", "two_earlier_on_third", "unchanged"]


def predictions():
    table = {}
    for pattern, (fx, start, end) in HOLDS.items():
        rules = FX14_RULES if fx == 14 else FX13_RULES
        table[pattern] = {
            rule: {
                step: (
                    fx14_prediction(rule, start, step) if fx == 14 else fx13_prediction(rule, step)
                )
                for step in range(start, end + 1)
            }
            for rule in rules
        }
    return table


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
        raise ValueError("The verified full-build state is required")
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
            if sound != SOUND
        ]
        operations.append(
            {
                "operation": "set_notes",
                "pattern": pattern,
                "sound": SOUND,
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
        if melodic_notes(target, pattern, SOUND) != RUN or step_effects(
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
    table = predictions()
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "fx-rules-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "sound": SOUND,
                "key_hz": KEY_HZ,
                "holds": {str(k): list(v) for k, v in HOLDS.items()},
                "control_pattern": CONTROL_PATTERN,
                "chain": CHAIN,
                "predictions": {
                    str(p): {
                        rule: {str(s): k for s, k in steps.items()} for rule, steps in rules.items()
                    }
                    for p, rules in table.items()
                },
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
                    "A rule holds for an effect when its prediction matches the key at 100 ms on every held step of every pattern using that effect",
                ],
                "limits": [
                    "Tempo 60, one melodic tone; FX 14 hold starts 3, 5, 7 and 9 only",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
