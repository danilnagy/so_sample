"""Register the voice release test: how much time left makes a voice stealable?

The voice stealing test suggested that a sounding voice is never cut while it has real
time left, and that a fifth note takes a voice with 84 ms or less remaining
(docs/voice-steal-results.md). This test varies the remaining time with pitch codes.

Source: the verified voice-steal state. Sound1 at key 13 plays the stored tone at half
rate: 200.0 Hz for 1.0 s. Sounds 2, 3 and 4 at key 1 last 334 ms at pitch 13; pitch code
P scales the length by 2^((13 - P) / 12). Pattern3 holds four scenarios of four steps:

  step 4k+1: Sound1 key 13 (long)
  step 4k+2: Sounds 2 3 4 at pitch P_k
  step 4k+3: Sound5 (the fifth note), while the long note has 500 ms left and the three
             short notes have REMAINING_MS[k] left: 417, 222, 84 or already ended (-14).

Pattern2 plays every voice alone. Models registered before the session (frozen method
scripts/polyphony_method_exploratory.py, three cycles), as presence at step 4k+3:
- never_steal: Sound5 plays only when a voice has ended (P=19); the long note and the
  short notes always continue.
- steal_nearest_end: Sound5 always plays; the long note continues; the short note with the
  highest sound number, 4, is the one taken (same-step priority order).
- release_under_100ms: Sound5 plays when the short notes have 84 ms or less left (P=13,
  19) and is dropped at 222 and 418 ms; nothing else is cut.
- steal_oldest: Sound5 always plays and the long note is cut.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain
from po33_re.formats.notes import step_parameters
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes, melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.polyphony_method_exploratory import SETTINGS
from scripts.prepare_polyphony_test import CHAIN, SOUND_ORDER, VOICES
from scripts.prepare_voice_steal_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.slim_drum_kits import slim_drum_kits

SOLO_PATTERN, SCENARIO_PATTERN = 2, 3
LONG_KEY, KEY13_SEMITONES = 13, -19
PITCHES = [1, 7, 13, 19]
KEY1_MS = 1000 * 0.5 / 2 ** (7 / 12)
REMAINING_MS = [round(KEY1_MS * 2 ** ((13 - p) / 12) - 250, 1) for p in PITCHES]
SHORT_SOUNDS = [2, 3, 4]
FIFTH = 5


def voice(sound, pitch=13, key=1):
    return f"{sound}" if pitch == 13 and key == 1 else f"{sound}k{key}p{pitch}"


VOICE_HZ = {
    voice(1, 13, LONG_KEY): VOICES[1] * 2 ** (KEY13_SEMITONES / 12),
    voice(FIFTH): VOICES[FIFTH],
    **{voice(s, p): VOICES[s] * 2 ** ((p - 13) / 12) for p in PITCHES for s in SHORT_SOUNDS},
}
VOICE_NAMES = list(VOICE_HZ)
LONG = voice(1, 13, LONG_KEY)
# Pattern2 solos: step -> (sound, key, pitch)
SOLO_NOTES = {1: (1, LONG_KEY, 13), 4: (FIFTH, 1, 13)}
for k, p in enumerate(PITCHES):
    for i, s in enumerate(SHORT_SOUNDS):
        SOLO_NOTES[5 + 3 * k + i] = (s, 1, p)
SOLO_STEPS = {voice(s, p, key): step for step, (s, key, p) in SOLO_NOTES.items()}
# Pattern3 scenarios: step -> {sound: (key, pitch)}
SCENARIO_NOTES = {}
for k, p in enumerate(PITCHES):
    SCENARIO_NOTES[4 * k + 1] = {1: (LONG_KEY, 13)}
    SCENARIO_NOTES[4 * k + 2] = {s: (1, p) for s in SHORT_SOUNDS}
    SCENARIO_NOTES[4 * k + 3] = {FIFTH: (1, 13)}
JUDGED_STEPS = [4 * k + 3 for k in range(len(PITCHES))]


def short_sounding(k):
    """Whether the short notes of scenario k still sound in the measurement window."""
    return REMAINING_MS[k] >= SETTINGS["window_ms"][0]


def predictions():
    table = {
        m: {} for m in ("never_steal", "steal_nearest_end", "release_under_100ms", "steal_oldest")
    }
    for k, p in enumerate(PITCHES):
        step = 4 * k + 3
        shorts = {voice(s, p): short_sounding(k) for s in SHORT_SOUNDS}
        ended = REMAINING_MS[k] < 0
        table["never_steal"][step] = {LONG: True, voice(FIFTH): ended, **shorts}
        table["steal_nearest_end"][step] = {
            LONG: True,
            voice(FIFTH): True,
            **{v: (present and not v.startswith("4")) for v, present in shorts.items()},
        }
        table["release_under_100ms"][step] = {
            LONG: True,
            voice(FIFTH): REMAINING_MS[k] < 100,
            **shorts,
        }
        table["steal_oldest"][step] = {LONG: False, voice(FIFTH): True, **shorts}
    return table


PREDICTIONS = predictions()
PLAN_DIRECTORY = "voice-release-plan-001"
DIRECTORY = "compiled-voice-release-001"
REGISTRATION = "voice-release-registration-001.json"
PLAYBACK_SECONDS = 26
CYCLES = 3
QUESTION = (
    "In the second pattern, did the fourth note of each group sometimes not play? (Enter to skip)"
)


def keys_and_pitches(pattern, sound):
    notes = (
        {step: {s: (key, p)} for step, (s, key, p) in SOLO_NOTES.items()}
        if pattern == SOLO_PATTERN
        else SCENARIO_NOTES
    )
    keys = [notes.get(step, {}).get(sound, (None, None))[0] for step in range(1, 17)]
    pitches = [notes.get(step, {}).get(sound, (None, None))[1] for step in range(1, 17)]
    return keys, pitches


def note_operations(pattern):
    operations = []
    for sound in SOUND_ORDER:
        if sound == 16:
            continue
        keys, _ = keys_and_pitches(pattern, sound)
        operations.append(
            {
                "operation": "set_melodic_notes_from" if sound <= 8 else "set_drum_notes",
                "pattern": pattern,
                "sound": sound,
                "keys": keys,
                "template_sound": 1,
            }
        )
    keys, _ = keys_and_pitches(pattern, 16)
    operations.append(
        {
            "operation": "set_drum_notes",
            "pattern": pattern,
            "sound": 16,
            "keys": keys,
            "template_sound": 1,
        }
    )
    for sound in (1, *SHORT_SOUNDS, FIFTH):
        _, pitches = keys_and_pitches(pattern, sound)
        if any(p is not None for p in pitches):
            operations.append(
                {
                    "operation": "set_step_parameters",
                    "pattern": pattern,
                    "sound": sound,
                    "parameter": "pitch",
                    "values": pitches,
                }
            )
    return operations


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any(
        (experiments / name).exists()
        for name in (PLAN_DIRECTORY, DIRECTORY, "voice-release-slim-hits-001")
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
        raise ValueError("The verified voice-steal state is required")
    if pattern_chain(decode_artifact(load_artifact(source_path))) != CHAIN:
        raise ValueError("The source chain must be 2, 3")
    # Shrink the drum kits first: key-1 tones unchanged, keys 2..16 silent, 4 pages each.
    slim_path, slim_reports = slim_drum_kits(source_path, experiments, "voice-release")
    source = decode_artifact(load_artifact(slim_path))
    operations = note_operations(SOLO_PATTERN) + note_operations(SCENARIO_PATTERN)
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(slim_path),
        "source_body_sha256": hashlib.sha256(source.encoded_body).hexdigest(),
        "operations": operations,
    }
    plan_folder = experiments / PLAN_DIRECTORY
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    folder = experiments / DIRECTORY
    report = compile_edit_plan(slim_path, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    for pattern in CHAIN:
        for sound in SOUND_ORDER:
            keys, pitches = keys_and_pitches(pattern, sound)
            reader = melodic_notes if sound <= 8 else drum_notes
            if reader(target, pattern, sound) != keys:
                raise ValueError(f"Pattern{pattern} Sound{sound} keys are not as planned")
            actual = [
                None if s is None else s["pitch"] for s in step_parameters(target, pattern, sound)
            ]
            if actual != pitches:
                raise ValueError(f"Pattern{pattern} Sound{sound} pitches are not as planned")
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
                "analysis_version": "voice-release-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "slim_kits": {
                    str(slot): {
                        "capacity_codes": r["allocation"]["capacity_codes"],
                        "import_report_sha256": sha256_file(
                            experiments
                            / f"import-drum{slot}-voice-release-slim-stage-001"
                            / "import-report.json"
                        ),
                    }
                    for slot, r in slim_reports.items()
                },
                "total_sample_codes": slim_reports[16]["allocation"][
                    "total_backing_capacity_codes"
                ],
                "pitches": PITCHES,
                "remaining_ms_at_fifth_note": REMAINING_MS,
                "voice_hz": VOICE_HZ,
                "solo_steps": SOLO_STEPS,
                "scenario_notes": {
                    str(k): {str(s): list(v) for s, v in notes.items()}
                    for k, notes in SCENARIO_NOTES.items()
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
                    "Four remaining times, 417, 222, 84 and -14 ms; the threshold is bracketed, not located",
                    "The fifth note is always Sound5, a higher number than the short notes",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "remaining_ms": REMAINING_MS}))


if __name__ == "__main__":
    main()
