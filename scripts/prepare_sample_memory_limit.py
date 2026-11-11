"""Register the sample-memory limit confirmation: exactly 241 pages (987136 codes).

The over-limit step offered 249 pages; the device kept an exact prefix of the restore
stream ending after 241 pages of sample data (Sound16's buffer cut to 69632 codes, its 15
key references dropped). This test offers exactly 241 pages in a complete layout.

Source: the verified 917504-code state (step 3). Two stages:
1. Sound16 gets 16 tones at 800 * 2^((k-1)/12) Hz, 4250 codes (181.3 ms) each; 68000
   codes round up to 69632, 17 pages.
2. Sound10 gets its own kit from the step-4 hits (102400 codes), as in step 4.
   The total becomes 987136 codes, 241 pages.

Through the public plan path, Pattern1 plays Sound16 key k on step k with Sound9's note
parameters, and Sound9's notes are cleared.

Registered before the session:
- limit_is_241_pages: the backup equals the target exactly, every reference included.
- Pitch: sound16_key_k predicts +100 (k-1) cents relative to step 1.
- Absolute: step 1 within 20 cents of 800 Hz.
- Duration: each step sounds for 181.3 ms within 5 ms.
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
from scripts.prepare_drum_kit_import_test import NATIVE_RATE, SETTINGS, hit_wav
from scripts.prepare_sample_memory_step3 import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_sample_memory_step3 import TOTAL as SOURCE_TOTAL
from scripts.prepare_sample_memory_step4 import HITS_DIRECTORY as SOUND10_HITS

LIMIT_PAGES = 241
TOTAL = LIMIT_PAGES * 4096
BASE_HZ, LENGTH, SOUND16_CAPACITY = 800.0, 4250, 69632
HITS_DIRECTORY = "drum16-limit-hits-001"
# Sound16 shrinks first so the running total never exceeds the limit.
STAGES = {16: "import-drum16-limit-stage-001", 10: "import-drum10-limit-stage-001"}
PLAN_DIRECTORY = "sample-memory-limit-plan-001"
DIRECTORY = "compiled-sample-memory-limit-001"
REGISTRATION = "sample-memory-limit-registration-001.json"
KEYS = list(range(1, 17))
FREQUENCIES = [round(BASE_HZ * 2 ** ((k - 1) / 12), 3) for k in KEYS]
PLAYBACK_SECONDS = 22
QUESTIONS = [
    "Did the PO-33 show ERR or anything unusual during or after the restore? Describe it (Enter for no)",
    "Did the pattern play a rising run of 16 beeps? (Enter to skip)",
]
MODELS = {"sound16_key_k": [100.0 * (k - 1) for k in KEYS]}
DURATION_MODEL_MS = [LENGTH / NATIVE_RATE * 1000] * 16


def absolute_decision(step1_hz):
    if step1_hz is None:
        return {"step1_cents_vs_hit1": None, "stored_rate": False}
    cents = 1200 * math.log2(step1_hz / BASE_HZ)
    return {
        "step1_cents_vs_hit1": cents,
        "stored_rate": abs(cents) <= SETTINGS["cents_tolerance"],
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    names = [HITS_DIRECTORY, PLAN_DIRECTORY, DIRECTORY, *STAGES.values()]
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any((experiments / name).exists() for name in names):
        raise ValueError("Fresh folders and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or observation["classification"] != "sound9_key_k"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified 917504-code state is required")
    sound10_hits = sorted((experiments / SOUND10_HITS).glob("key*.wav"))
    pins = json.loads((experiments / "sample-memory-registration-004.json").read_text())["hits"]
    if [sha256_file(p) for p in sound10_hits] != [h["sha256"] for h in pins]:
        raise ValueError("Sound10 hits changed since their registration")
    hits_folder = experiments / HITS_DIRECTORY
    hits_folder.mkdir()
    sound16_hits = []
    for key, frequency in enumerate(FREQUENCIES, 1):
        path = hits_folder / f"key{key:02d}-{frequency:.0f}hz-{LENGTH}codes.wav"
        write_bytes(path, hit_wav(frequency, LENGTH))
        sound16_hits.append(path)
    hits = {10: sound10_hits, 16: sound16_hits}
    capacities = {10: 102400, 16: SOUND16_CAPACITY}
    current, allocations = source_path, {}
    for slot, stage in STAGES.items():
        report = compile_drum_kit_import(
            current,
            hits[slot],
            experiments / stage,
            slot,
            capacity=capacities[slot],
            allowed_slots=(slot,),
            total_limit=TOTAL,
        )
        allocations[slot] = report["allocation"]
        current = experiments / stage / "edited.symbols.npz"
    if allocations[10]["total_backing_capacity_codes"] != TOTAL or SOURCE_TOTAL + 69632 != TOTAL:
        raise ValueError("Total capacity is not the planned value")
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
                "sound": 16,
                "keys": KEYS,
                "template_sound": 9,
            },
            {
                "operation": "set_drum_notes",
                "pattern": 1,
                "sound": 9,
                "keys": [None] * 16,
                "template_sound": 16,
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
    if drum_notes(target, 1, 16) != KEYS or drum_notes(target, 1, 9) != [None] * 16:
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
                "import_stages": ["../" + stage for stage in STAGES.values()],
                "playback_seconds": PLAYBACK_SECONDS,
                "observation_questions": QUESTIONS,
                "hardware_restore": {"status": "not_run"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "sample-memory-limit-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "total_capacity_codes": TOTAL,
                "total_pages": LIMIT_PAGES,
                "sound16_hits": [
                    {"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p), "hz": f}
                    for p, f in zip(sound16_hits, FREQUENCIES, strict=True)
                ],
                "sound16_hit_codes": LENGTH,
                "allocations": {str(k): v for k, v in allocations.items()},
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "hypotheses": {
                    "limit_is_241_pages": "the backup equals the target exactly, all 16 Sound16 references included",
                },
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "absolute_hz": BASE_HZ,
                "duration_method_settings": DURATION_SETTINGS,
                "duration_method_script_sha256": sha256_file(
                    root / "scripts/drum_slice_duration_method.py"
                ),
                "duration_model_ms": DURATION_MODEL_MS,
                "decision": [
                    "limit_is_241_pages holds when the backup equals the compiled target exactly",
                    "Pitch: sound16_key_k holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                    "Absolute: step 1 within 20 cents of 800 Hz",
                    "Duration: every step within 5 ms of 181.3 ms in the median and in at least 4 of 5 loops",
                ],
                "limits": [
                    "The limit is measured with this pattern and settings content; whether pattern or other data shares the same memory is not tested",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "total_codes": TOTAL}))


if __name__ == "__main__":
    main()
