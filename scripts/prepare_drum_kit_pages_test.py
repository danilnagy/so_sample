"""Register a drum import into empty Sound12 with page-rounded capacities.

Source: the verified drum-kit-import state (Sound11 holds 16 imported tones in the
device's 102400-code buffer; total sample capacity 266240 codes).

Stages:
1. Re-import the same 16 Sound11 hits with the default capacity: 58000 codes rounded up
   to whole 4096-code pages, 61440. Total drops to 225280.
2. Import 16 new hits into empty Sound12 (sound ids 56..71). Hit k is a tone at
   500 * 2^((k-1)/12) Hz, 2375 codes (101.3 ms) long; 38000 codes round up to 40960.
   Total returns to 266240, the largest total already carried by the device.
3. Through the public plan path: Sound12 key k on step k of Pattern1, with Sound11's note
   parameters, then Sound11's notes are cleared.

Two new claims: page-rounded capacities other than the device's own 102400, and a kit
written into an empty drum slot. The backup diff separates them if reception fails.

Models, registered before the session:
- Pitch, cents relative to step 1: sound12_key_k predicts +100 (k-1).
- Absolute pitch of step 1: within 20 cents of 500 Hz (stored rate).
- Duration: each step sounds for 2375 / 23437.5 s within 5 ms.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.drum_import import compile_drum_kit_import
from po33_re.edits import compile_edit_plan
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes
from po33_re.modem.symbols import load_artifact
from scripts.drum_slice_duration_method import SETTINGS as DURATION_SETTINGS
from scripts.prepare_drum_kit_import_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_drum_kit_import_test import HITS_DIRECTORY as SOUND11_HITS
from scripts.prepare_drum_kit_import_test import LENGTHS as SOUND11_LENGTHS
from scripts.prepare_drum_kit_import_test import NATIVE_RATE, SETTINGS, hit_wav

HITS_DIRECTORY = "drum12-hits-001"
STAGE11 = "import-drum11-pages-stage-001"
STAGE12 = "import-drum12-stage-001"
PLAN_DIRECTORY = "drum-kit-pages-plan-001"
DIRECTORY = "compiled-drum-kit-pages-001"
REGISTRATION = "drum-kit-pages-registration-001.json"
FREQUENCIES = [round(500 * 2 ** ((k - 1) / 12), 3) for k in range(1, 17)]
LENGTH = 2375
CAPACITIES = {11: 61440, 12: 40960}
KEYS = list(range(1, 17))
PLAYBACK_SECONDS = 22
QUESTION = "Did the pattern play a rising run of 16 short beeps? (Enter to skip)"
MODELS = {"sound12_key_k": [100.0 * (k - 1) for k in KEYS]}
DURATION_MODEL_MS = [LENGTH / NATIVE_RATE * 1000] * 16


def absolute_decision(step1_hz):
    if step1_hz is None:
        return {"step1_cents_vs_hit1": None, "stored_rate": False}
    cents = 1200 * math.log2(step1_hz / FREQUENCIES[0])
    return {
        "step1_cents_vs_hit1": cents,
        "stored_rate": abs(cents) <= SETTINGS["cents_tolerance"],
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    names = (HITS_DIRECTORY, STAGE11, STAGE12, PLAN_DIRECTORY, DIRECTORY)
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any((experiments / name).exists() for name in names):
        raise ValueError("Fresh folders and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or observation["classification"] != "new_kit_key_k"
        or not observation["stops_at_window_end"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified drum-kit-import state is required")
    sound11_hits = sorted((experiments / SOUND11_HITS).glob("key*.wav"))
    registered = json.loads((experiments / "drum-kit-import-registration-001.json").read_text())[
        "hits"
    ]
    if [sha256_file(p) for p in sound11_hits] != [h["sha256"] for h in registered]:
        raise ValueError("Sound11 hits changed since their registration")
    report11 = compile_drum_kit_import(source_path, sound11_hits, experiments / STAGE11, 11)
    hits_folder = experiments / HITS_DIRECTORY
    hits_folder.mkdir()
    paths = []
    for key, frequency in enumerate(FREQUENCIES, 1):
        path = hits_folder / f"key{key:02d}-{frequency:.0f}hz-{LENGTH}codes.wav"
        write_bytes(path, hit_wav(frequency, LENGTH))
        paths.append(path)
    stage11 = experiments / STAGE11 / "edited.symbols.npz"
    report12 = compile_drum_kit_import(
        stage11, paths, experiments / STAGE12, 12, allowed_slots=(12,)
    )
    allocations = {11: report11["allocation"], 12: report12["allocation"]}
    if (
        {slot: a["capacity_codes"] for slot, a in allocations.items()} != CAPACITIES
        or [end - start for start, end in allocations[11]["windows"]] != SOUND11_LENGTHS
        or report12["allocation"]["total_backing_capacity_codes"] != 266240
    ):
        raise ValueError("Stages do not have the planned capacities and windows")
    stage12 = experiments / STAGE12 / "edited.symbols.npz"
    stage_frame = decode_artifact(load_artifact(stage12))
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(stage12),
        "source_body_sha256": hashlib.sha256(stage_frame.encoded_body).hexdigest(),
        "operations": [
            {
                "operation": "set_drum_notes",
                "pattern": 1,
                "sound": 12,
                "keys": KEYS,
                "template_sound": 11,
            },
            {
                "operation": "set_drum_notes",
                "pattern": 1,
                "sound": 11,
                "keys": [None] * 16,
                "template_sound": 12,
            },
        ],
    }
    plan_folder = experiments / PLAN_DIRECTORY
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    folder = experiments / DIRECTORY
    report = compile_edit_plan(stage12, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    if drum_notes(target, 1, 12) != KEYS or drum_notes(target, 1, 11) != [None] * 16:
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
                "import_stages": ["../" + STAGE11, "../" + STAGE12],
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
                "analysis_version": "drum-kit-pages-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "sound12_hits": [
                    {"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p), "hz": f}
                    for p, f in zip(paths, FREQUENCIES, strict=True)
                ],
                "sound12_hit_codes": LENGTH,
                "stage_reports_sha256": {
                    "11": sha256_file(experiments / STAGE11 / "import-report.json"),
                    "12": sha256_file(experiments / STAGE12 / "import-report.json"),
                },
                "allocations": {str(k): v for k, v in allocations.items()},
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "absolute_hz": FREQUENCIES[0],
                "duration_method_settings": DURATION_SETTINGS,
                "duration_method_script_sha256": sha256_file(
                    root / "scripts/drum_slice_duration_method.py"
                ),
                "duration_model_ms": DURATION_MODEL_MS,
                "decision": [
                    "The backup must equal the compiled target exactly, including both kits and their capacities",
                    "Pitch: sound12_key_k holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                    "Absolute: step 1 within 20 cents of 500 Hz",
                    "Duration: every step within 5 ms of 101.3 ms in the median and in at least 4 of 5 loops",
                ],
                "limits": [
                    "Two page-rounded capacities (61440, 40960) and one empty slot (Sound12); others follow by the same rule but are not played",
                    "Total sample capacity equals the largest total already observed, 266240 codes; larger totals are not tested",
                    "Sound11 is checked by exact reception only; its notes are cleared in this pattern",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "capacities": CAPACITIES}))


if __name__ == "__main__":
    main()
