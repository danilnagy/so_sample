"""Register a sample import into Sound7, a slot never imported before, played in a pattern.

Stages, all from the verified volume-zero state:
1. Generate a 600 Hz, 0.3 s, 48 kHz PCM tone (2 ms fades).
2. Import it into empty Sound7 with the slot-generic importer (32768-code capacity, owner
   byte 6), keeping every other packet.
3. Through the public plan path: uniform volume 36 on Sound3, Sound3 key 1 on odd steps,
   and Sound7 key 1 on even steps with Sound3's note parameters.

Sound3's notes play a 750.0 Hz tone stored in Sound1's buffer. At the same key and pitch
code, the imported 600 Hz tone should sound 1200*log2(600/750) = -386.3 cents relative to
Sound3, whatever the device's fixed transposition is. The backup must equal the target.
"""

import argparse
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import melodic_notes
from po33_re.modem.symbols import load_artifact
from po33_re.sample_import import compile_sample_import
from scripts.prepare_pitch_law_confirm import SETTINGS

SOURCE_EXPERIMENT = "compiled-volume-zero-001"
TONE_DIRECTORY = "sound7-import-tone-001"
STAGE_DIRECTORY = "import-sound7-stage-001"
PLAN_DIRECTORY = "sound7-import-plan-001"
DIRECTORY = "compiled-sound7-import-001"
REGISTRATION = "sound7-import-registration-001.json"
TONE_HZ, TONE_SECONDS, TONE_LEVEL, FADE_SECONDS = 600.0, 0.3, 0.5, 0.002
SOUND3_TONE_HZ = 750.0
CAPACITY = 32768
SOUND3_KEYS = [1, None] * 8
SOUND7_KEYS = [None, 1] * 8
PLAYBACK_SECONDS = 22
QUESTION = "Did every other note sound lower, like a second instrument? (Enter to skip)"
SOUND7_CENTS = 1200 * math.log2(TONE_HZ / SOUND3_TONE_HZ)
MODELS = {"imported_tone_on_even_steps": [0.0 if s % 2 else SOUND7_CENTS for s in range(1, 17)]}


def tone_wav():
    rate = 48000
    t = np.arange(round(TONE_SECONDS * rate)) / rate
    tone = TONE_LEVEL * np.sin(2 * np.pi * TONE_HZ * t)
    fade = round(FADE_SECONDS * rate)
    ramp = np.linspace(0, 1, fade)
    tone[:fade] *= ramp
    tone[-fade:] *= ramp[::-1]
    buffer = io.BytesIO()
    sf.write(buffer, tone, rate, subtype="PCM_16", format="WAV")
    return buffer.getvalue()


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folders = [
        root / "experiments" / name
        for name in (TONE_DIRECTORY, STAGE_DIRECTORY, PLAN_DIRECTORY, DIRECTORY)
    ]
    registration_path = root / "experiments" / REGISTRATION
    if registration_path.exists() or any(f.exists() for f in folders):
        raise ValueError("Fresh folders and registration required")
    tone_folder, stage_folder, plan_folder, folder = folders
    source_folder = root / "experiments" / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified volume-zero state is required")
    tone_folder.mkdir()
    tone_path = tone_folder / "tone-600hz-0.3s.wav"
    write_bytes(tone_path, tone_wav())
    import_report = compile_sample_import(
        source_path, tone_path, stage_folder, 7, None, CAPACITY, allowed_slots=(7,)
    )
    stage_artifact = stage_folder / "edited.symbols.npz"
    stage_frame = decode_artifact(load_artifact(stage_artifact))
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(stage_artifact),
        "source_body_sha256": hashlib.sha256(stage_frame.encoded_body).hexdigest(),
        "operations": [
            {
                "operation": "set_step_parameters",
                "pattern": 1,
                "sound": 3,
                "parameter": "volume",
                "values": [36] * 16,
            },
            {"operation": "set_melodic_notes", "pattern": 1, "sound": 3, "keys": SOUND3_KEYS},
            {
                "operation": "set_melodic_notes_from",
                "pattern": 1,
                "sound": 7,
                "keys": SOUND7_KEYS,
                "template_sound": 3,
            },
        ],
    }
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    report = compile_edit_plan(stage_artifact, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    if melodic_notes(target, 1, 3) != SOUND3_KEYS or melodic_notes(target, 1, 7) != SOUND7_KEYS:
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
                "import_stage": "../" + STAGE_DIRECTORY,
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
                "analysis_version": "sound7-import-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "tone": {
                    "path": tone_path.relative_to(root).as_posix(),
                    "sha256": sha256_file(tone_path),
                    "hz": TONE_HZ,
                    "seconds": TONE_SECONDS,
                },
                "import_report_sha256": sha256_file(stage_folder / "import-report.json"),
                "import_allocation": import_report["allocation"],
                "stage_artifact_sha256": plan["source_artifact_sha256"],
                "plan_sha256": sha256_file(plan_path),
                "compile_report_sha256": sha256_file(folder / "compile-report.json"),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "sound3_tone_hz": SOUND3_TONE_HZ,
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "decision": [
                    "The backup must equal the compiled target exactly, including every imported Sound7 code",
                    "Pitches are measured with the frozen grid method 50-90 ms after each grid onset; cents relative to step 1",
                    "The model holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                ],
                "limits": [
                    "One import into empty Sound7 with a 32768-code capacity; other slots and capacities are not tested here",
                    "Total serialized sample capacity stays inside the 172032-code calibration budget",
                ],
            }
        ),
    )
    print(
        json.dumps(
            {"ready": True, "folder": DIRECTORY, "allocation": import_report["allocation"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
