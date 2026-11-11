"""Register imports into all eight melodic slots, including slots that borrow Sound1.

Source: the verified long-melodic state. Sound1 owns a buffer that Sound2, Sound3 and
Sound8 (melodic) and Sound9, Sound10 (drum kits) reference. Stages, in order:
1. Sound9 and Sound10 get small kits of their own: 16 hits of 1000 codes, 16384 codes.
2. Melodic Sound2, Sound3 and Sound8 get their own buffers (borrowed replacement).
3. Sound1, now unreferenced, and Sound4..7 are replaced.

Every melodic slot s gets a 0.5 s tone at 400 * 2^(150 (s-1) / 1200) Hz (11719 codes,
three pages, 12288 codes). The total becomes 745472 codes.

Through the public plan path, Pattern1 plays Sound s key 1 on step 2s-1, with Sound6's
note parameters (pitch code 13). Each note lasts 0.5 s / 2^(7/12) = 334 ms, so it is still
sounding in the measurement window of the next, empty step.

Models registered before the session (frozen grid method, 15-55 ms after each grid onset):
- slot_s_plays_its_tone: steps 2s-1 and 2s sound 150 (s-1) cents above step 1.
- Absolute: step 1 within 20 cents of 400 * 2^(7/12) = 599.3 Hz.
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
from po33_re.drum_import import compile_drum_kit_import
from po33_re.edits import compile_edit_plan
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import melodic_notes
from po33_re.modem.symbols import load_artifact
from po33_re.sample_import import DEVICE_SAMPLE_LIMIT, compile_sample_import
from scripts.prepare_drum_kit_import_test import SETTINGS, hit_wav
from scripts.prepare_long_melodic_test import DIRECTORY as SOURCE_EXPERIMENT

SLOTS = list(range(1, 9))
ORDER = [2, 3, 8, 1, 4, 5, 6, 7]
TONE_HZ = {s: round(400 * 2 ** (150 * (s - 1) / 1200), 3) for s in SLOTS}
TONE_SECONDS, LEVEL, FADE_SECONDS, WAV_RATE = 0.5, 0.5, 0.002, 48000
NATIVE_CODES, CAPACITY = 11719, 12288
DRUM_HIT_CODES, DRUM_CAPACITY = 1000, 16384
TOTAL = 745472
FILES_DIRECTORY = "all-melodic-slots-files-001"
PLAN_DIRECTORY = "all-melodic-slots-plan-001"
DIRECTORY = "compiled-all-melodic-slots-001"
REGISTRATION = "all-melodic-slots-registration-001.json"
TRANSPOSE_CENTS = 700.0
PLAYBACK_SECONDS = 22
QUESTION = "Did the pattern play eight rising notes, one on every other step? (Enter to skip)"
MODELS = {"slot_s_plays_its_tone": [150.0 * ((step - 1) // 2) for step in range(1, 17)]}


def stage_name(kind, slot):
    return f"import-{kind}{slot}-all-melodic-stage-001"


def keys_for(slot):
    return [1 if step == 2 * slot - 1 else None for step in range(1, 17)]


def tone_wav(frequency):
    t = np.arange(round(TONE_SECONDS * WAV_RATE)) / WAV_RATE
    tone = LEVEL * np.sin(2 * np.pi * frequency * t)
    fade = round(FADE_SECONDS * WAV_RATE)
    ramp = np.linspace(0, 1, fade)
    tone[:fade] *= ramp
    tone[-fade:] *= ramp[::-1]
    buffer = io.BytesIO()
    sf.write(buffer, tone, WAV_RATE, subtype="PCM_16", format="WAV")
    return buffer.getvalue()


def absolute_decision(step1_hz):
    if step1_hz is None:
        return {"step1_cents_vs_expected": None, "holds": False}
    cents = 1200 * math.log2(step1_hz / TONE_HZ[1]) - TRANSPOSE_CENTS
    return {"step1_cents_vs_expected": cents, "holds": abs(cents) <= SETTINGS["cents_tolerance"]}


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    stages = [stage_name("drum", s) for s in (9, 10)] + [stage_name("sound", s) for s in ORDER]
    names = [FILES_DIRECTORY, PLAN_DIRECTORY, DIRECTORY, *stages]
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any((experiments / name).exists() for name in names):
        raise ValueError("Fresh folders and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or observation["classification"] != "whole_sample_plays_in_order"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified long-melodic state is required")
    files = experiments / FILES_DIRECTORY
    files.mkdir()
    current, reports, inputs = source_path, {}, {}
    for slot in (9, 10):
        paths = []
        for key in range(1, 17):
            path = files / f"sound{slot}-key{key:02d}.wav"
            write_bytes(path, hit_wav(300.0 * 2 ** ((key - 1) / 12), DRUM_HIT_CODES))
            paths.append(path)
        inputs[slot] = paths
        stage = experiments / stage_name("drum", slot)
        reports[slot] = compile_drum_kit_import(
            current,
            paths,
            stage,
            slot,
            allowed_slots=(slot,),
            total_limit=DEVICE_SAMPLE_LIMIT,
        )
        current = stage / "edited.symbols.npz"
    for slot in ORDER:
        path = files / f"sound{slot}-{TONE_HZ[slot]:.0f}hz.wav"
        write_bytes(path, tone_wav(TONE_HZ[slot]))
        inputs[slot] = [path]
        stage = experiments / stage_name("sound", slot)
        reports[slot] = compile_sample_import(
            current,
            path,
            stage,
            slot,
            None,
            None,
            (slot,),
            DEVICE_SAMPLE_LIMIT,
            max_frames=NATIVE_CODES,
            page_capacity=True,
            replace_borrowed=True,
        )
        current = stage / "edited.symbols.npz"
    allocations = {slot: report["allocation"] for slot, report in reports.items()}
    if (
        any(allocations[s]["capacity_codes"] != DRUM_CAPACITY for s in (9, 10))
        or any(allocations[s]["capacity_codes"] != CAPACITY for s in SLOTS)
        or [allocations[s]["source_record_was_borrowed"] for s in (2, 3, 8)] != [True] * 3
        or allocations[ORDER[-1]]["total_backing_capacity_codes"] != TOTAL
    ):
        raise ValueError("Stages do not have the planned capacities, layouts and total")
    stage_frame = decode_artifact(load_artifact(current))
    operations = [
        {
            "operation": "set_melodic_notes_from",
            "pattern": 1,
            "sound": slot,
            "keys": keys_for(slot),
            "template_sound": 6,
        }
        for slot in SLOTS
        if slot != 6
    ]
    operations.append(
        {
            "operation": "set_melodic_notes_from",
            "pattern": 1,
            "sound": 6,
            "keys": keys_for(6),
            "template_sound": 1,
        }
    )
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(current),
        "source_body_sha256": hashlib.sha256(stage_frame.encoded_body).hexdigest(),
        "operations": operations,
    }
    plan_folder = experiments / PLAN_DIRECTORY
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    folder = experiments / DIRECTORY
    report = compile_edit_plan(current, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    if any(melodic_notes(target, 1, slot) != keys_for(slot) for slot in SLOTS):
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
                "import_stages": ["../" + name for name in stages],
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
                "analysis_version": "all-melodic-slots-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "tone_hz": {str(k): v for k, v in TONE_HZ.items()},
                "inputs": {
                    str(slot): [
                        {"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p)}
                        for p in paths
                    ]
                    for slot, paths in inputs.items()
                },
                "allocations": {str(k): v for k, v in allocations.items()},
                "total_capacity_codes": TOTAL,
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "absolute_expected_hz": TONE_HZ[1] * 2 ** (TRANSPOSE_CENTS / 1200),
                "decision": [
                    "The backup must equal the compiled target exactly, every buffer and reference included",
                    "slot_s_plays_its_tone holds when all 16 steps are within 20 cents in the five-loop median and in at least 4 of 5 loops",
                    "Absolute: step 1 within 20 cents of 599.3 Hz",
                ],
                "limits": [
                    "One short tone per melodic slot at key 1 and pitch code 13; Sound9 and Sound10 kits are checked by exact reception only",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "total_codes": TOTAL}))


if __name__ == "__main__":
    main()
