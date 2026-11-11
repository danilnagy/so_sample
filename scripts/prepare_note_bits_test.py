"""Register the note bits test: pitch code 0 and the unknown primary bit 5.

Source: the verified voice-release state (slim kits; Sound1 holds a 400 Hz, 0.5 s tone
that plays at 599.3 Hz for 334 ms at key 1, pitch 13). Through the public plan path the
chain becomes [2] and Pattern2 plays Sound1 key 1 on every step with the pitch codes and
bit-5 flags in STEPS; Pattern3's notes are cleared.

Pitch code 0 is tested like filter, resonance and volume 0: a step with code 0 follows a
locked step. Bit 5 is set on three notes that otherwise copy the note before them.

Models of the per-step pitch relative to step 1 (frozen grid method, 20 ms windows 100,
110 and 120 ms after each grid onset):
- zero_holds_last_pitch: code-0 steps repeat the previous step's pitch; bit 5 changes nothing.
- zero_is_pitch_13: code-0 steps play at 0 cents.
- zero_is_below_code_1: code-0 steps play at -1300 cents.
Bit 5, compared with the matching note one step earlier: bit5_inert holds when every pair
is within 20 cents, 1.5 dB and 5 ms of duration (duration on the pitch-25 pairs only,
whose 167 ms fits a step). If the device clears bit 5, the backup will differ from the
target only in those bits; that outcome is classified bit5_cleared_by_device.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain
from po33_re.formats.notes import step_parameters, unknown_bits
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.drum_slice_duration_method import SETTINGS as DURATION_SETTINGS
from scripts.pattern1_key_scale_grid_method import SETTINGS as GRID_SETTINGS
from scripts.polyphony_method_exploratory import SETTINGS as LEVEL_SETTINGS
from scripts.prepare_polyphony_test import SOUND_ORDER, VOICES
from scripts.prepare_voice_release_test import DIRECTORY as SOURCE_EXPERIMENT

PATTERN = 2
CHAIN = [PATTERN]
# step -> (pitch code, bit 5); 0 means unlocked pitch.
STEPS = {
    1: (13, 0),
    2: (19, 0),
    3: (0, 0),
    4: (7, 0),
    5: (0, 0),
    6: (25, 0),
    7: (25, 1),
    8: (13, 0),
    9: (13, 1),
    10: (1, 0),
    11: (0, 0),
    12: (25, 0),
    13: (25, 1),
    14: (13, 0),
    15: (0, 0),
    16: (13, 0),
}
BIT5_PAIRS = [(7, 6), (9, 8), (13, 12)]
DURATION_PAIRS = [(7, 6), (13, 12)]
SETTINGS = {**GRID_SETTINGS, "window_starts_ms": [100.0, 110.0, 120.0]}
BASE_HZ = VOICES[1]


def held_pitches():
    """Effective pitch code per step under zero_holds_last_pitch."""
    held, last = {}, 13
    for step in range(1, 17):
        if step not in STEPS:
            continue
        code, _ = STEPS[step]
        last = code if code else last
        held[step] = last
    return held


def cents(code):
    return 100.0 * (code - 13)


MODELS = {
    "zero_holds_last_pitch": [cents(held_pitches()[s]) for s in range(1, 17)],
    "zero_is_pitch_13": [cents(STEPS[s][0]) if STEPS[s][0] else 0.0 for s in range(1, 17)],
    "zero_is_below_code_1": [cents(STEPS[s][0]) if STEPS[s][0] else -1300.0 for s in range(1, 17)],
}
EXPECTED_HZ = {s: BASE_HZ * 2 ** (cents(held_pitches()[s]) / 1200) for s in STEPS}
PLAN_DIRECTORY = "note-bits-plan-001"
DIRECTORY = "compiled-note-bits-001"
REGISTRATION = "note-bits-registration-001.json"
PLAYBACK_SECONDS = 22
QUESTION = (
    "Did any note sound different from its neighbour in an odd way, or go missing? (Enter to skip)"
)


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
        raise ValueError("The verified voice-release state is required")
    source = decode_artifact(load_artifact(source_path))
    operations = []
    for pattern in (2, 3):
        # Sound1 has notes with one parameter set in both patterns; it is the template.
        for sound in SOUND_ORDER:
            if sound == 1:
                continue
            operations.append(
                {
                    "operation": "set_melodic_notes_from" if sound <= 8 else "set_drum_notes",
                    "pattern": pattern,
                    "sound": sound,
                    "keys": [None] * 16,
                    "template_sound": 1,
                }
            )
        operations.append(
            {
                "operation": "set_melodic_notes",
                "pattern": pattern,
                "sound": 1,
                "keys": [1 if pattern == PATTERN and s in STEPS else None for s in range(1, 17)],
            }
        )
    operations += [
        {
            "operation": "set_step_parameters",
            "pattern": PATTERN,
            "sound": 1,
            "parameter": "pitch",
            "values": [STEPS[s][0] if s in STEPS else None for s in range(1, 17)],
        },
        {
            "operation": "set_note_unknown_bits",
            "pattern": PATTERN,
            "sound": 1,
            "values": [STEPS[s][1] if s in STEPS else None for s in range(1, 17)],
        },
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
    params = step_parameters(target, PATTERN, 1)
    if (
        melodic_notes(target, PATTERN, 1) != [1 if s in STEPS else None for s in range(1, 17)]
        or [None if p is None else p["pitch"] for p in params]
        != [STEPS[s][0] if s in STEPS else None for s in range(1, 17)]
        or unknown_bits(target, PATTERN, 1)
        != [STEPS[s][1] if s in STEPS else None for s in range(1, 17)]
        or pattern_chain(target) != CHAIN
    ):
        raise ValueError("Compiled target does not hold the planned notes")
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
                "analysis_version": "note-bits-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "steps": {str(k): list(v) for k, v in STEPS.items()},
                "bit5_pairs": BIT5_PAIRS,
                "duration_pairs": DURATION_PAIRS,
                "expected_hz_under_hold": {str(k): v for k, v in EXPECTED_HZ.items()},
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "duration_method_settings": DURATION_SETTINGS,
                "duration_method_script_sha256": sha256_file(
                    root / "scripts/drum_slice_duration_method.py"
                ),
                "level_method_settings": LEVEL_SETTINGS,
                "level_method_script_sha256": sha256_file(
                    root / "scripts/polyphony_method_exploratory.py"
                ),
                "models_cents": MODELS,
                "bit5_tolerances": {"cents": 20.0, "db": 1.5, "ms": 5.0},
                "decision": [
                    "Reception: the backup equals the target exactly, or differs only in bit 5 of the flagged cells (bit5_cleared_by_device)",
                    "Pitch: a model holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                    "bit5_inert holds when each flagged note matches the note before it within 20 cents, 1.5 dB, and 5 ms on the pitch-25 pairs",
                ],
                "limits": [
                    "One melodic sound at key 1; bit 5 on drum notes is not tested",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "held": held_pitches()}))


if __name__ == "__main__":
    main()
