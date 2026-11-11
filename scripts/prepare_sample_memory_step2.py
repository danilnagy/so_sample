"""Register the second sample-memory step: total 815104 codes (34.8 s of 40 s advertised).

Source: the verified 675840-code state. Three stages, each an already verified kind of
import, with only the total changing:
1. Sound11 gets its registered 16 hits again with the full 102400-code capacity (+40960).
2. Sound12 gets its registered 16 hits again with the full 102400-code capacity (+61440).
3. Empty melodic Sound6 gets a 1.2 s, 700 Hz tone with a 36864-code capacity (+36864).

Through the public plan path, Pattern1 then plays Sound11 key k on step k with Sound16's
note parameters, and Sound16's notes are cleared. Sound11's hits and window lengths are
those of the verified drum-kit import, so its registered models apply unchanged:
- Pitch: new_kit_key_k predicts -100 (k-1) cents relative to step 1.
- Absolute: step 1 within 20 cents of 1500 Hz.
- Duration: each step sounds for its window length within 5 ms.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.drum_import import compile_drum_kit_import
from po33_re.edits import compile_edit_plan
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes
from po33_re.modem.symbols import load_artifact
from po33_re.sample_import import compile_sample_import
from scripts.drum_slice_duration_method import SETTINGS as DURATION_SETTINGS
from scripts.prepare_drum_kit_import_test import (
    ABSOLUTE_MODELS,
    DURATION_MODEL_MS,
    MODELS,
    SETTINGS,
)
from scripts.prepare_drum_kit_import_test import HITS_DIRECTORY as SOUND11_HITS
from scripts.prepare_drum_kit_pages_test import HITS_DIRECTORY as SOUND12_HITS
from scripts.prepare_drum_memory_test import DIRECTORY as SOURCE_EXPERIMENT

SOURCE_TOTAL = 675840
CAPACITIES = {11: 102400, 12: 102400, 6: 36864}
TOTAL = SOURCE_TOTAL + (102400 - 61440) + (102400 - 40960) + 36864
TONE_DIRECTORY = "sound6-memory-tone-001"
STAGES = {11: "import-drum11-memory2-stage-001", 12: "import-drum12-memory2-stage-001"}
STAGE6 = "import-sound6-memory2-stage-001"
PLAN_DIRECTORY = "sample-memory-plan-002"
DIRECTORY = "compiled-sample-memory-002"
REGISTRATION = "sample-memory-registration-002.json"
TONE_HZ, TONE_SECONDS, TONE_LEVEL, FADE_SECONDS = 700.0, 1.2, 0.5, 0.002
KEYS = list(range(1, 17))
PLAYBACK_SECONDS = 22
QUESTION = "Did the restore finish without ERR, and the pattern play a falling run of 16 beeps that get longer? (Enter to skip)"


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


def registered_hits(experiments, directory, registration, key):
    paths = sorted((experiments / directory).glob("key*.wav"))
    pins = json.loads((experiments / registration).read_text())[key]
    if [sha256_file(p) for p in paths] != [h["sha256"] for h in pins]:
        raise ValueError(f"Hits in {directory} changed since registration")
    return paths


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    names = [TONE_DIRECTORY, STAGE6, PLAN_DIRECTORY, DIRECTORY, *STAGES.values()]
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any((experiments / name).exists() for name in names):
        raise ValueError("Fresh folders and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or observation["total_capacity_codes"] != SOURCE_TOTAL
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified 675840-code state is required")
    hits = {
        11: registered_hits(
            experiments, SOUND11_HITS, "drum-kit-import-registration-001.json", "hits"
        ),
        12: registered_hits(
            experiments, SOUND12_HITS, "drum-kit-pages-registration-001.json", "sound12_hits"
        ),
    }
    current, reports = source_path, {}
    for slot, stage in STAGES.items():
        reports[slot] = compile_drum_kit_import(
            current,
            hits[slot],
            experiments / stage,
            slot,
            capacity=CAPACITIES[slot],
            allowed_slots=(slot,),
            total_limit=TOTAL,
        )
        current = experiments / stage / "edited.symbols.npz"
    tone_folder = experiments / TONE_DIRECTORY
    tone_folder.mkdir()
    tone_path = tone_folder / "tone-700hz-1.2s.wav"
    write_bytes(tone_path, tone_wav())
    reports[6] = compile_sample_import(
        current, tone_path, experiments / STAGE6, 6, None, CAPACITIES[6], (6,), TOTAL
    )
    if reports[6]["allocation"]["total_backing_capacity_codes"] != TOTAL:
        raise ValueError("Total capacity is not the planned value")
    current = experiments / STAGE6 / "edited.symbols.npz"
    stage_frame = decode_artifact(load_artifact(current))
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(current),
        "source_body_sha256": hashlib.sha256(stage_frame.encoded_body).hexdigest(),
        "operations": [
            {
                "operation": "set_drum_notes",
                "pattern": 1,
                "sound": 11,
                "keys": KEYS,
                "template_sound": 16,
            },
            {
                "operation": "set_drum_notes",
                "pattern": 1,
                "sound": 16,
                "keys": [None] * 16,
                "template_sound": 11,
            },
        ],
    }
    plan_folder = experiments / PLAN_DIRECTORY
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    folder = experiments / DIRECTORY
    report = compile_edit_plan(current, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    if drum_notes(target, 1, 11) != KEYS or drum_notes(target, 1, 16) != [None] * 16:
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
                "import_stages": ["../" + STAGES[11], "../" + STAGES[12], "../" + STAGE6],
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
                "analysis_version": "sample-memory-registration-0.2",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "total_capacity_codes": TOTAL,
                "capacities": {str(k): v for k, v in CAPACITIES.items()},
                "sound6_tone": {
                    "path": tone_path.relative_to(root).as_posix(),
                    "sha256": sha256_file(tone_path),
                    "hz": TONE_HZ,
                    "seconds": TONE_SECONDS,
                },
                "stage_reports_sha256": {
                    "11": sha256_file(experiments / STAGES[11] / "import-report.json"),
                    "12": sha256_file(experiments / STAGES[12] / "import-report.json"),
                    "6": sha256_file(experiments / STAGE6 / "import-report.json"),
                },
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "absolute_models_cents_vs_hit1": ABSOLUTE_MODELS,
                "duration_method_settings": DURATION_SETTINGS,
                "duration_method_script_sha256": sha256_file(
                    root / "scripts/drum_slice_duration_method.py"
                ),
                "duration_model_ms": DURATION_MODEL_MS,
                "decision": [
                    "The backup must equal the compiled target exactly, every sample buffer included",
                    "Pitch: new_kit_key_k holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                    "Absolute: step 1 within 20 cents of 1500 Hz",
                    "Duration: every step within 5 ms of its window length in the median and in at least 4 of 5 loops",
                ],
                "limits": [
                    "One total, 815104 codes; totals between it and the advertised 937500 are not tested",
                    "Only Sound11 is played; the other buffers are checked by exact reception",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "total_codes": TOTAL}))


if __name__ == "__main__":
    main()
