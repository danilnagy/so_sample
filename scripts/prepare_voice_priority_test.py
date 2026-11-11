"""Register the voice priority test: which four sounds play when more are stacked?

Source: the verified polyphony state, with fourteen distinct tones (eight melodic sounds
7 semitones up at key 1; drums 11..16 at 1500, 500, 300, 400, 1200 and 1350 Hz). Pattern2
plays each sound alone. Through the public plan path, Pattern3's stacks become eight
sets of five or more sounds, chosen so that candidate rules disagree:

  step 1: 1 2 3 4 11      step 9: 1 11 12 13 14
  step 3: 1 2 3 4 16      step 11: 1 2 11 12 13
  step 5: 1 2 3 4 5       step 13: 11 12 13 14 15
  step 7: 4 5 6 8 7       step 15: 1 2 3 11 12 13 14 15 16

Hypotheses registered before the session (frozen method
scripts/polyphony_method_exploratory.py, three chain cycles; a voice is present within
10 dB of its solo):
- four_voices: every stack sounds exactly four voices.
- lowest_sounds_win: the four lowest sound numbers play.
- highest_sounds_win: the four highest play.
- drums_win: drums before melodic sounds, lowest number first within a class.
(Melodic sounds always have the lower numbers, so "melodic first" is lowest_sounds_win.)
The measured set of present sounds per stack is reported whatever the outcome.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes, melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.polyphony_method_exploratory import SETTINGS
from scripts.prepare_polyphony_test import CHAIN, SOLO_STEPS, SOUND_ORDER, VOICES
from scripts.prepare_polyphony_test import DIRECTORY as SOURCE_EXPERIMENT

STACK_PATTERN = 3
STACKS = {
    1: [1, 2, 3, 4, 11],
    3: [1, 2, 3, 4, 16],
    5: [1, 2, 3, 4, 5],
    7: [4, 5, 6, 7, 8],
    9: [1, 11, 12, 13, 14],
    11: [1, 2, 11, 12, 13],
    13: [11, 12, 13, 14, 15],
    15: [1, 2, 3, 11, 12, 13, 14, 15, 16],
}
VOICE_COUNT = 4
PLAN_DIRECTORY = "voice-priority-plan-001"
DIRECTORY = "compiled-voice-priority-001"
REGISTRATION = "voice-priority-registration-001.json"
PLAYBACK_SECONDS = 26
CYCLES = 3
QUESTION = "Did every chord sound like four notes, and which ones seemed missing? (Enter to skip)"


def is_drum(sound):
    return sound >= 9


def predicted(rule, sounds):
    if rule == "lowest_sounds_win":
        order = sorted(sounds)
    elif rule == "highest_sounds_win":
        order = sorted(sounds, reverse=True)
    elif rule == "drums_win":
        order = sorted(sounds, key=lambda s: (not is_drum(s), s))
    else:
        raise ValueError(rule)
    return sorted(order[:VOICE_COUNT])


RULES = ["lowest_sounds_win", "highest_sounds_win", "drums_win"]


def keys_for(sound):
    return [1 if sound in STACKS.get(step, []) else None for step in range(1, 17)]


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
        raise ValueError("The verified polyphony state is required")
    source = decode_artifact(load_artifact(source_path))
    if pattern_chain(source) != CHAIN:
        raise ValueError("The source chain must be 2, 3")
    operations = []
    for sound in SOUND_ORDER:
        if sound == 16:
            continue
        operations.append(
            {
                "operation": "set_melodic_notes_from" if sound <= 8 else "set_drum_notes",
                "pattern": STACK_PATTERN,
                "sound": sound,
                "keys": keys_for(sound),
                "template_sound": 16,
            }
        )
    operations.append(
        {
            "operation": "set_drum_notes",
            "pattern": STACK_PATTERN,
            "sound": 16,
            "keys": keys_for(16),
            "template_sound": 16,
        }
    )
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
    for sound in SOUND_ORDER:
        reader = melodic_notes if sound <= 8 else drum_notes
        if reader(target, STACK_PATTERN, sound) != keys_for(sound):
            raise ValueError(f"Pattern3 Sound{sound} is not as planned")
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
                "analysis_version": "voice-priority-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "voices_hz": {str(k): v for k, v in VOICES.items()},
                "solo_steps": {str(k): v for k, v in SOLO_STEPS.items()},
                "stacks": {str(k): v for k, v in STACKS.items()},
                "voice_count": VOICE_COUNT,
                "rule_predictions": {
                    rule: {str(step): predicted(rule, sounds) for step, sounds in STACKS.items()}
                    for rule in RULES
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
                    "A rule holds when every stack's majority present set equals its prediction",
                ],
                "limits": [
                    "Sounds triggered on the same step at 60 BPM; stealing across steps is not tested",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
