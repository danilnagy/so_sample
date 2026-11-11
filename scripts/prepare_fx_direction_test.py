"""Register the FX direction test: effects on a sample whose pitch changes through the note.

FX 1, 2 and 15 change nothing on a pure tone (docs/fx-loop-results.md), and FX 3, 4 and 12
extend a note without saying how. Sound6 holds a 1.0 s sample of four segments at 400,
500, 600 and 700 Hz, windowed to segment 3 since the sample-window test. Here the window
returns to the whole sample, so a key-1 note plays segments 1..4 in 667 ms.

Patterns 1..8 play Sound6 key 1 on steps 1, 5, 9 and 13 with FX 1, 2, 15, 3, 4, 12, 11 and
13 held on steps 5..16, so each pattern's first note is plain and the next three are
under the effect. Pattern 9 is the control. Chain 1..9, tempo 60, one cycle of 36 s.

Models of the segment sequence over the five windows (20, 190, 360, 530, 700 ms) for the
notes under each effect, registered before the session:
- forward: 1, 2, 3, 4, silence.
- reverse: 4, 3, 2, 1, silence.
- hold_first: 1, 1, 1, 1 and anything after: the first segment looped.
Each effect is classified as the model matching all three held notes, or described.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.effects import step_effects
from po33_re.formats.globals import pattern_chain, swing, tempo
from po33_re.formats.packets import decode_artifact, sound_data
from po33_re.formats.patterns import melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.fx_direction_method import SEGMENT_HZ, SETTINGS
from scripts.prepare_fx_loop_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_sample_window_test import NATIVE_CODES

HELD = {1: 1, 2: 2, 3: 15, 4: 3, 5: 4, 6: 12, 7: 11, 8: 13}
CONTROL_PATTERN = 9
CHAIN = list(range(1, 10))
NOTE_STEPS = [1, 5, 9, 13]
HOLD_STEPS = list(range(5, 17))
TEMPO = 60
MODELS = {
    "forward": [1, 2, 3, 4, None],
    "reverse": [4, 3, 2, 1, None],
    "hold_first": [1, 1, 1, 1, "any"],
}
PLAN_DIRECTORY = "fx-direction-plan-001"
DIRECTORY = "compiled-fx-direction-001"
REGISTRATION = "fx-direction-registration-001.json"
PLAYBACK_SECONDS = 40
QUESTION = (
    "Did any pattern play the rising sample backwards, or stuck on one pitch? (Enter to skip)"
)


def effects_for(pattern):
    fx = HELD.get(pattern)
    return [fx if fx and step in HOLD_STEPS else None for step in range(1, 17)]


def keys():
    return [1 if step in NOTE_STEPS else None for step in range(1, 17)]


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
        raise ValueError("The verified loop-test state is required")
    source = decode_artifact(load_artifact(source_path))
    parameters = {"pitch": 13, "volume": 36, "filter": 63, "resonance": 1}
    operations = [{"operation": "set_sample_window", "sound": 6, "start": 0, "end": NATIVE_CODES}]
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
            if sound != 6
        ]
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
    header = sound_data(target, 5)[:9]
    if (
        int.from_bytes(header[:4], "little") != 0
        or int.from_bytes(header[4:8], "little") != NATIVE_CODES
    ):
        raise ValueError("Sound6 window is not the whole sample")
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
                "analysis_version": "fx-direction-registration-0.1",
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
                "segment_hz": SEGMENT_HZ,
                "models": MODELS,
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/fx_direction_method.py"),
                "descriptor_method_script_sha256": sha256_file(
                    root / "scripts/fx_descriptor_method.py"
                ),
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "The control pattern's four notes and every pattern's first note read forward",
                    "Each held effect is classified as the model matching all three held notes, else described",
                ],
                "limits": [
                    "One sample and one key at tempo 60; effects that depend on content are described in this setting only",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
