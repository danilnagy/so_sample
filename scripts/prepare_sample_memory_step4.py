"""Register the fourth sample-memory step: total 1019904 codes, past the advertised 40 s.

Source: the verified 917504-code state (39.1 s). Drum Sound10's 16 keys borrow windows
of Sound1's buffer; the importer gives Sound10 its own 102400-code kit of 6375-code tones
(272 ms) at 350 * 2^((k-1)/12) Hz. The total becomes 1019904 codes, 43.5 s at 23437.5 Hz,
against the advertised 40 s (937500 codes).

Through the public plan path, Pattern1 plays Sound10 key k on step k with Sound9's note
parameters, and Sound9's notes are cleared.

Hypotheses registered before the session:
- advertised_limit_rejects: the device does not hold the target; the backup differs.
- accepted: the backup equals the target exactly.

The outcome is classified from the backup as accepted_exact, kept_previous (equals the
917504-code source), empty (no sample buffers), other (any other content, summarized), or
not_decoded. Only when accepted_exact is Sound10 played and measured: +100 (k-1) cents
relative to step 1, and step 1 within 20 cents of 350 Hz.
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
from scripts.prepare_sample_memory_step3 import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_sample_memory_step3 import TOTAL as SOURCE_TOTAL

SLOT, BASE_HZ, LENGTH, CAPACITY = 10, 350.0, 6375, 102400
TOTAL = SOURCE_TOTAL + CAPACITY
ADVERTISED_CODES = 937500
HITS_DIRECTORY = "drum10-memory-hits-001"
STAGE = "import-drum10-memory4-stage-001"
PLAN_DIRECTORY = "sample-memory-plan-004"
DIRECTORY = "compiled-sample-memory-004"
REGISTRATION = "sample-memory-registration-004.json"
KEYS = list(range(1, 17))
FREQUENCIES = [round(BASE_HZ * 2 ** ((k - 1) / 12), 3) for k in KEYS]
PLAYBACK_SECONDS = 22
QUESTIONS = [
    "Did the PO-33 show ERR or anything unusual during or after the restore? Describe it (Enter for no)",
    "Did the pattern play a rising run of 16 beeps? (Enter to skip)",
]
MODELS = {"sound10_key_k": [100.0 * (k - 1) for k in KEYS]}
OUTCOMES = ["accepted_exact", "kept_previous", "empty", "other", "not_decoded"]


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
    names = [HITS_DIRECTORY, STAGE, PLAN_DIRECTORY, DIRECTORY]
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
    hits_folder = experiments / HITS_DIRECTORY
    hits_folder.mkdir()
    paths = []
    for key, frequency in enumerate(FREQUENCIES, 1):
        path = hits_folder / f"key{key:02d}-{frequency:.0f}hz.wav"
        write_bytes(path, hit_wav(frequency, LENGTH))
        paths.append(path)
    import_report = compile_drum_kit_import(
        source_path,
        paths,
        experiments / STAGE,
        SLOT,
        capacity=CAPACITY,
        allowed_slots=(SLOT,),
        total_limit=TOTAL,
    )
    allocation = import_report["allocation"]
    if (
        allocation["source_layout"] != "references_to_sound_id_0"
        or allocation["total_backing_capacity_codes"] != TOTAL
    ):
        raise ValueError("Stage does not have the planned layout and total")
    stage = experiments / STAGE / "edited.symbols.npz"
    stage_frame = decode_artifact(load_artifact(stage))
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(stage),
        "source_body_sha256": hashlib.sha256(stage_frame.encoded_body).hexdigest(),
        "operations": [
            {
                "operation": "set_drum_notes",
                "pattern": 1,
                "sound": SLOT,
                "keys": KEYS,
                "template_sound": 9,
            },
            {
                "operation": "set_drum_notes",
                "pattern": 1,
                "sound": 9,
                "keys": [None] * 16,
                "template_sound": SLOT,
            },
        ],
    }
    plan_folder = experiments / PLAN_DIRECTORY
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    folder = experiments / DIRECTORY
    report = compile_edit_plan(stage, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    if drum_notes(target, 1, SLOT) != KEYS or drum_notes(target, 1, 9) != [None] * 16:
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
                "import_stages": ["../" + STAGE],
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
                "analysis_version": "sample-memory-registration-0.4",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "total_capacity_codes": TOTAL,
                "advertised_codes": ADVERTISED_CODES,
                "hits": [
                    {"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p), "hz": f}
                    for p, f in zip(paths, FREQUENCIES, strict=True)
                ],
                "hit_codes": LENGTH,
                "allocation": allocation,
                "stage_report_sha256": sha256_file(experiments / STAGE / "import-report.json"),
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "hypotheses": {
                    "advertised_limit_rejects": "the backup differs from the target",
                    "accepted": "the backup equals the target exactly",
                },
                "outcomes": OUTCOMES,
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "absolute_hz": BASE_HZ,
                "decision": [
                    "Outcome from the accepted backup: accepted_exact, kept_previous, empty, other, or not_decoded",
                    "Only if accepted_exact: sound10_key_k holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops; step 1 within 20 cents of 350 Hz",
                ],
                "limits": [
                    "One total above the advertised limit; the exact limit is not located by this test",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "total_codes": TOTAL}))


if __name__ == "__main__":
    main()
