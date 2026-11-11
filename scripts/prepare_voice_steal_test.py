"""Register the voice stealing test: does a fifth note cut an older note or get dropped?

Source: the verified voice-priority state (four voices; fourteen distinct tones). Melodic
key 13 plays 12 semitones below key 1, so a 0.5 s melodic tone lasts 1.0 s, four steps at
60 BPM. Through the public plan path, Pattern2 becomes solos and Pattern3 four scenarios:

  A  step 1: Sound1 key 13 (long)   step 2: Sounds 2 3 4    step 3: Sound 5
  B  step 5: Sound1 key 13 (long)   step 6: Sounds 2 3     step 7: Sound 5  (control, 4 voices)
  C  step 9: Sound8 key 13 (long)   step 10: Sounds 11 12 14   step 11: Sound 1
  D  step 13: Sound8 key 13 (long)  step 15: Sounds 1 2 3 4

A key-1 melodic note lasts 334 ms and ends 84 ms into the next step, before the 100 to
240 ms measurement window, so the fifth note always arrives while four voices sound.

Models registered before the session (frozen method scripts/polyphony_method_exploratory.py,
three chain cycles), as the presence of the long note and the new note after the overflow:
- drop_new: the fifth note does not play; the long note continues.
- steal_oldest: the fifth note plays and the long note, the oldest voice, is cut.
- lowest_sound_wins: the lowest sound numbers keep playing (C: Sound 1 plays and Sound 8
  continues; D: Sound 8 is cut).
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
from scripts.prepare_polyphony_test import CHAIN, SOUND_ORDER, VOICES
from scripts.prepare_voice_priority_test import DIRECTORY as SOURCE_EXPERIMENT

SOLO_PATTERN, SCENARIO_PATTERN = 2, 3
LONG_KEY = 13
# voice name -> frequency; "1k13" is Sound1 at key 13 (one octave below key 1).
VOICE_HZ = {
    "1k13": VOICES[1] / 2,
    "8k13": VOICES[8] / 2,
    **{str(s): VOICES[s] for s in (1, 2, 3, 4, 5, 11, 12, 14)},
}
VOICE_NAMES = list(VOICE_HZ)
SOLO_STEPS = {
    "1k13": 1,
    "8k13": 5,
    "1": 9,
    "2": 10,
    "3": 11,
    "4": 12,
    "5": 13,
    "11": 14,
    "12": 15,
    "14": 16,
}
# Pattern3 notes: step -> {sound: key}
SCENARIO_NOTES = {
    1: {1: LONG_KEY},
    2: {2: 1, 3: 1, 4: 1},
    3: {5: 1},
    5: {1: LONG_KEY},
    6: {2: 1, 3: 1},
    7: {5: 1},
    9: {8: LONG_KEY},
    10: {11: 1, 12: 1, 14: 1},
    11: {1: 1},
    13: {8: LONG_KEY},
    15: {1: 1, 2: 1, 3: 1, 4: 1},
}
# Predictions: step -> {voice: present} per model. Only listed voices are judged.
PREDICTIONS = {
    "drop_new": {
        2: {"1k13": True, "2": True, "3": True, "4": True},
        3: {"1k13": True, "5": False},
        4: {"1k13": True},
        7: {"1k13": True, "5": True},
        8: {"1k13": True},
        10: {"8k13": True, "11": True, "12": True, "14": True},
        11: {"8k13": True, "1": False},
        12: {"8k13": True},
        15: {"8k13": True, "1": True, "2": True, "3": True, "4": False},
        16: {"8k13": True},
    },
    "steal_oldest": {
        2: {"1k13": True, "2": True, "3": True, "4": True},
        3: {"1k13": False, "5": True},
        4: {"1k13": False},
        7: {"1k13": True, "5": True},
        8: {"1k13": True},
        10: {"8k13": True, "11": True, "12": True, "14": True},
        11: {"8k13": False, "1": True},
        12: {"8k13": False},
        15: {"8k13": False, "1": True, "2": True, "3": True, "4": True},
        16: {"8k13": False},
    },
    "lowest_sound_wins": {
        2: {"1k13": True, "2": True, "3": True, "4": True},
        3: {"1k13": True, "5": False},
        4: {"1k13": True},
        7: {"1k13": True, "5": True},
        8: {"1k13": True},
        10: {"8k13": True, "11": True, "12": True, "14": True},
        11: {"8k13": True, "1": True},
        12: {"8k13": True},
        15: {"8k13": False, "1": True, "2": True, "3": True, "4": True},
        16: {"8k13": False},
    },
}
JUDGED_STEPS = sorted({step for p in PREDICTIONS.values() for step in p})
PLAN_DIRECTORY = "voice-steal-plan-001"
DIRECTORY = "compiled-voice-steal-001"
REGISTRATION = "voice-steal-registration-001.json"
PLAYBACK_SECONDS = 26
CYCLES = 3
QUESTION = "In the second pattern, did long low notes get cut short when other notes came in? (Enter to skip)"


def solo_notes():
    """step -> {sound: key} for Pattern2, from the voice names."""
    notes = {}
    for name, step in SOLO_STEPS.items():
        sound, _, key = name.partition("k")
        notes[step] = {int(sound): int(key) if key else 1}
    return notes


def keys_for(pattern, sound):
    notes = solo_notes() if pattern == SOLO_PATTERN else SCENARIO_NOTES
    return [notes.get(step, {}).get(sound) for step in range(1, 17)]


def note_operations(pattern):
    operations = []
    for sound in SOUND_ORDER:
        if sound == 16:
            continue
        operations.append(
            {
                "operation": "set_melodic_notes_from" if sound <= 8 else "set_drum_notes",
                "pattern": pattern,
                "sound": sound,
                "keys": keys_for(pattern, sound),
                "template_sound": 16,
            }
        )
    operations.append(
        {
            "operation": "set_drum_notes",
            "pattern": pattern,
            "sound": 16,
            "keys": keys_for(pattern, 16),
            "template_sound": 16,
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
        or not observation["checks"]["session_target_exact"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified voice-priority state is required")
    source = decode_artifact(load_artifact(source_path))
    if pattern_chain(source) != CHAIN:
        raise ValueError("The source chain must be 2, 3")
    operations = note_operations(SOLO_PATTERN) + note_operations(SCENARIO_PATTERN)
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
                "analysis_version": "voice-steal-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "voice_hz": VOICE_HZ,
                "solo_steps": SOLO_STEPS,
                "scenario_notes": {
                    str(k): {str(s): key for s, key in v.items()} for k, v in SCENARIO_NOTES.items()
                },
                "predictions": {
                    m: {str(k): v for k, v in p.items()} for m, p in PREDICTIONS.items()
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
                    "A model holds when every listed voice's majority presence over three cycles matches its prediction",
                ],
                "limits": [
                    "Overflow by one or four notes at 60 BPM; other timings and same-sound retriggers are not tested",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "judged_steps": JUDGED_STEPS}))


if __name__ == "__main__":
    main()
