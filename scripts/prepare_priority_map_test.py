"""Register the priority map test: which drum sounds outrank melodic Sound4 on a shared step?

The voice priority tests found that the four lowest sound numbers play, except that
Sound11 beat Sound4 while Sound16 lost to it (docs/voice-priority-results.md). This test
pits each drum 11..16 against Sounds 1..4, and Sound11 against Sound5.

Source: the verified swing-law state. Through the public plan path: swing back to 0,
Sound6 and Sound7 notes cleared, Pattern2 plays each of the eleven voices alone on steps
1..11, Pattern3 holds the eight stacks on odd steps, chain 2, 3.

Hypotheses registered before the session (frozen method
scripts/polyphony_method_exploratory.py, three cycles):
- four_voices: every stack sounds exactly four.
- lowest_sounds_win: the four lowest numbers play in every stack.
- sound11_outranks_4_and_5: Sound11 ranks right after Sound3; everything else by number.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain, swing
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes, melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.polyphony_method_exploratory import SETTINGS
from scripts.prepare_polyphony_test import VOICES as ALL_VOICES
from scripts.prepare_swing_law_test import DIRECTORY as SOURCE_EXPERIMENT

SOLO_PATTERN, STACK_PATTERN = 2, 3
CHAIN = [SOLO_PATTERN, STACK_PATTERN]
SOUND_ORDER = [1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 16]
VOICES = {s: ALL_VOICES[s] for s in SOUND_ORDER}
SOLO_STEPS = {sound: step for step, sound in enumerate(SOUND_ORDER, 1)}
STACKS = {
    1: [1, 2, 3, 4, 11],
    3: [1, 2, 3, 4, 12],
    5: [1, 2, 3, 4, 13],
    7: [1, 2, 3, 4, 14],
    9: [1, 2, 3, 4, 15],
    11: [1, 2, 3, 4, 16],
    13: [1, 2, 3, 5, 11],
    15: [2, 3, 4, 5, 11],
}
VOICE_COUNT = 4
RANKINGS = {
    "lowest_sounds_win": list(range(1, 17)),
    "sound11_outranks_4_and_5": [1, 2, 3, 11, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16],
}
PLAN_DIRECTORY = "priority-map-plan-001"
DIRECTORY = "compiled-priority-map-001"
REGISTRATION = "priority-map-registration-001.json"
PLAYBACK_SECONDS = 26
CYCLES = 3
QUESTION = "Did every chord sound like four notes? (Enter to skip)"


def predicted(rule, sounds):
    order = RANKINGS[rule]
    return sorted(sorted(sounds, key=order.index)[:VOICE_COUNT])


def keys_for(pattern, sound):
    if pattern == SOLO_PATTERN:
        return [1 if SOLO_STEPS.get(sound) == step else None for step in range(1, 17)]
    return [1 if sound in STACKS.get(step, []) else None for step in range(1, 17)]


def note_operations(pattern, template):
    operations = []
    for sound in SOUND_ORDER:
        operations.append(
            {
                "operation": "set_melodic_notes_from" if sound <= 8 else "set_drum_notes",
                "pattern": pattern,
                "sound": sound,
                "keys": keys_for(pattern, sound),
                "template_sound": template,
            }
        )
    return operations


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
        or observation["classification"] != "linear_in_code"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified swing-law state is required")
    source = decode_artifact(load_artifact(source_path))
    if pattern_chain(source) != [SOLO_PATTERN]:
        raise ValueError("The source chain must be [2]")
    # Sound6 has identical notes on every step of Pattern2 and serves as the template there.
    operations = [{"operation": "set_swing_byte", "value": 0}]
    operations += note_operations(SOLO_PATTERN, 6)
    operations.append(
        {"operation": "set_melodic_notes", "pattern": SOLO_PATTERN, "sound": 6, "keys": [None] * 16}
    )
    # Pattern3 is empty in the source, so copy the solos there to provide a template.
    operations.append(
        {
            "operation": "copy_pattern",
            "source_pattern": SOLO_PATTERN,
            "destination_pattern": STACK_PATTERN,
        }
    )
    operations += note_operations(STACK_PATTERN, 1)
    for pattern in CHAIN:
        for sound in (6, 7, 8):
            if sound == 6 and pattern == SOLO_PATTERN:
                continue
            operations.append(
                {
                    "operation": "set_melodic_notes",
                    "pattern": pattern,
                    "sound": sound,
                    "keys": [None] * 16,
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
    for pattern in CHAIN:
        for sound in SOUND_ORDER:
            reader = melodic_notes if sound <= 8 else drum_notes
            if reader(target, pattern, sound) != keys_for(pattern, sound):
                raise ValueError(f"Pattern{pattern} Sound{sound} is not as planned")
        if any(melodic_notes(target, pattern, s) != [None] * 16 for s in (6, 7, 8)):
            raise ValueError(f"Pattern{pattern} still has notes on Sound6..8")
    if pattern_chain(target) != CHAIN or swing(target) != 0:
        raise ValueError("Chain or swing is not as planned")
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
                "analysis_version": "priority-map-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "voices_hz": {str(k): v for k, v in VOICES.items()},
                "solo_steps": {str(k): v for k, v in SOLO_STEPS.items()},
                "stacks": {str(k): v for k, v in STACKS.items()},
                "rankings": RANKINGS,
                "rule_predictions": {
                    rule: {str(step): predicted(rule, sounds) for step, sounds in STACKS.items()}
                    for rule in RANKINGS
                },
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/polyphony_method_exploratory.py"
                ),
                "cycles_measured": CYCLES,
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "four_voices holds when every stack's majority count over three cycles is 4",
                    "A ranking holds when every stack's majority present set equals its prediction",
                ],
                "limits": [
                    "Sounds 1..5 and 11..16 only; Sound9 and Sound10 hits are too short for the window",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
