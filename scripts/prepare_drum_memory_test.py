"""Register a sample-memory step: four full drum kits raise the total to 675840 codes.

Source: the verified page-capacity state (total sample capacity 266240 codes, the largest
the device has carried). Empty drum Sound13..16 each get a 16-hit kit of 6375-code tones
(272 ms), 102000 codes rounded up to the device's own 102400-code capacity. The total
becomes 675840 codes, 28.8 s at 23437.5 Hz, against the 40 s the device advertises
(937500 codes).

Kit for slot N uses tones at BASE[N] * 2^((k-1)/12) Hz. Pattern1 then plays Sound16, the
last kit written, key k on step k with Sound12's note parameters; Sound12's notes are
cleared. Each hit outlasts its 250 ms step, so the next note cuts it; duration is not
measured.

Registered before the session:
- Reception: the backup equals the compiled target exactly, all six kits included.
- Pitch: sound16_key_k predicts +100 (k-1) cents relative to step 1.
- Absolute: step 1 within 20 cents of 800 Hz.
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
from scripts.prepare_drum_kit_import_test import SETTINGS, hit_wav
from scripts.prepare_drum_kit_pages_test import DIRECTORY as SOURCE_EXPERIMENT

SLOTS = (13, 14, 15, 16)
BASE = {13: 300.0, 14: 400.0, 15: 600.0, 16: 800.0}
LENGTH = 6375
CAPACITY = 102400
TOTAL = 266240 + len(SLOTS) * CAPACITY
HITS_DIRECTORY = "drum-memory-hits-001"
PLAN_DIRECTORY = "drum-memory-plan-001"
DIRECTORY = "compiled-drum-memory-001"
REGISTRATION = "drum-memory-registration-001.json"
KEYS = list(range(1, 17))
PLAYBACK_SECONDS = 22
QUESTION = "Did the restore finish without ERR, and the pattern play a rising run of 16 beeps? (Enter to skip)"
MODELS = {"sound16_key_k": [100.0 * (k - 1) for k in KEYS]}


def frequencies(slot):
    return [round(BASE[slot] * 2 ** ((k - 1) / 12), 3) for k in KEYS]


def stage_name(slot):
    return f"import-drum{slot}-memory-stage-001"


def absolute_decision(step1_hz):
    if step1_hz is None:
        return {"step1_cents_vs_hit1": None, "stored_rate": False}
    cents = 1200 * math.log2(step1_hz / BASE[16])
    return {
        "step1_cents_vs_hit1": cents,
        "stored_rate": abs(cents) <= SETTINGS["cents_tolerance"],
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    names = [HITS_DIRECTORY, PLAN_DIRECTORY, DIRECTORY, *map(stage_name, SLOTS)]
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any((experiments / name).exists() for name in names):
        raise ValueError("Fresh folders and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or observation["classification"] != "sound12_key_k"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified page-capacity state is required")
    hits_folder = experiments / HITS_DIRECTORY
    hits_folder.mkdir()
    current, reports, hits = source_path, {}, {}
    for slot in SLOTS:
        paths = []
        for key, frequency in enumerate(frequencies(slot), 1):
            path = hits_folder / f"sound{slot}-key{key:02d}-{frequency:.0f}hz.wav"
            write_bytes(path, hit_wav(frequency, LENGTH))
            paths.append(path)
        hits[slot] = paths
        stage = experiments / stage_name(slot)
        reports[slot] = compile_drum_kit_import(
            current, paths, stage, slot, allowed_slots=(slot,), total_limit=TOTAL
        )
        if reports[slot]["allocation"]["capacity_codes"] != CAPACITY:
            raise ValueError(f"Sound{slot} did not get the planned capacity")
        current = stage / "edited.symbols.npz"
    if reports[SLOTS[-1]]["allocation"]["total_backing_capacity_codes"] != TOTAL:
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
                "template_sound": 12,
            },
            {
                "operation": "set_drum_notes",
                "pattern": 1,
                "sound": 12,
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
    if drum_notes(target, 1, 16) != KEYS or drum_notes(target, 1, 12) != [None] * 16:
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
                "import_stages": ["../" + stage_name(slot) for slot in SLOTS],
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
                "analysis_version": "drum-memory-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "total_capacity_codes": TOTAL,
                "hits": {
                    str(slot): [
                        {"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p)}
                        for p in paths
                    ]
                    for slot, paths in hits.items()
                },
                "hit_codes": LENGTH,
                "frequencies_hz": {str(slot): frequencies(slot) for slot in SLOTS},
                "stage_reports_sha256": {
                    str(slot): sha256_file(experiments / stage_name(slot) / "import-report.json")
                    for slot in SLOTS
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
                "absolute_hz": BASE[16],
                "decision": [
                    "The backup must equal the compiled target exactly, all six kits and capacities included",
                    "Pitch: sound16_key_k holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                    "Absolute: step 1 within 20 cents of 800 Hz",
                ],
                "limits": [
                    "One total, 675840 codes; the device limit itself is not located by this test",
                    "Only Sound16's kit is played; Sound13..15 are checked by exact reception",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "total_codes": TOTAL}))


if __name__ == "__main__":
    main()
