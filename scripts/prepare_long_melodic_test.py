"""Register a long melodic import: a 4.0 s sample in Sound6 with a page-rounded capacity.

The melodic importer was verified up to 30912 native codes (1.32 s) in the device's own
capacities. This test imports a 4.0 s sample, 93750 codes, into Sound6 with 94208 codes
(23 pages), replacing its 36864-code tone. The sample is four phase-continuous 1.0 s
segments at 400, 500, 600 and 700 Hz, so its order and length are audible.

Source: the verified 815104-code state; the total becomes 872448 codes, within the
241-page limit. Through the public plan path, Pattern1 gets one Sound6 key-1 note on
step 1, with Sound11's note parameters (pitch code 13, volume 36); Sound11's notes are
cleared. At 60 BPM the pattern loops every 4.0 s.

Models registered before the session (melodic key 1 at pitch 13 plays the stored audio
7 semitones up, docs/sound7-import-results.md):
- whole_sample_plays: the note lasts 4.0 s / 2^(7/12) = 2669.7 ms, within 10 ms.
- quarters_in_order: the four quarters sound at 400, 500, 600 and 700 Hz times 2^(7/12),
  within 20 cents.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes, melodic_notes
from po33_re.modem.symbols import load_artifact
from po33_re.sample_import import DEVICE_SAMPLE_LIMIT, compile_sample_import
from scripts.long_note_method import SETTINGS
from scripts.prepare_sample_memory_step2 import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_sample_memory_step2 import TOTAL as SOURCE_TOTAL

SEGMENT_HZ = [400.0, 500.0, 600.0, 700.0]
SEGMENT_SECONDS, LEVEL, FADE_SECONDS, WAV_RATE = 1.0, 0.5, 0.002, 48000
NATIVE_CODES, CAPACITY = 93750, 94208
TOTAL = SOURCE_TOTAL - 36864 + CAPACITY
TONE_DIRECTORY = "long-melodic-sample-001"
STAGE = "import-sound6-long-stage-001"
PLAN_DIRECTORY = "long-melodic-plan-001"
DIRECTORY = "compiled-long-melodic-001"
REGISTRATION = "long-melodic-registration-001.json"
TRANSPOSE = 2 ** (7 / 12)
EXPECTED_MS = len(SEGMENT_HZ) * SEGMENT_SECONDS * 1000 / TRANSPOSE
EXPECTED_HZ = [f * TRANSPOSE for f in SEGMENT_HZ]
NOTES = [1] + [None] * 15
PLAYBACK_SECONDS = 22
QUESTION = "Did each loop play one long note that steps up four times? (Enter to skip)"


def sample_wav():
    count = round(SEGMENT_SECONDS * WAV_RATE)
    phase, pieces = 0.0, []
    for frequency in SEGMENT_HZ:
        steps = phase + 2 * np.pi * frequency * np.arange(1, count + 1) / WAV_RATE
        pieces.append(np.sin(np.r_[phase, steps[:-1]]))
        phase = float(steps[-1] % (2 * np.pi))
    tone = LEVEL * np.concatenate(pieces)
    fade = round(FADE_SECONDS * WAV_RATE)
    ramp = np.linspace(0, 1, fade)
    tone[:fade] *= ramp
    tone[-fade:] *= ramp[::-1]
    buffer = io.BytesIO()
    sf.write(buffer, tone, WAV_RATE, subtype="PCM_16", format="WAV")
    return buffer.getvalue()


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    names = [TONE_DIRECTORY, STAGE, PLAN_DIRECTORY, DIRECTORY]
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
        raise ValueError("The verified 815104-code state is required")
    tone_folder = experiments / TONE_DIRECTORY
    tone_folder.mkdir()
    sample_path = tone_folder / "four-segments-400-700hz-4s.wav"
    write_bytes(sample_path, sample_wav())
    import_report = compile_sample_import(
        source_path,
        sample_path,
        experiments / STAGE,
        6,
        None,
        None,
        (6,),
        DEVICE_SAMPLE_LIMIT,
        max_frames=NATIVE_CODES,
        page_capacity=True,
    )
    allocation = import_report["allocation"]
    if (
        allocation["capacity_codes"] != CAPACITY
        or allocation["endpoint"] != NATIVE_CODES
        or allocation["total_backing_capacity_codes"] != TOTAL
    ):
        raise ValueError("Import does not have the planned length, capacity and total")
    stage = experiments / STAGE / "edited.symbols.npz"
    stage_frame = decode_artifact(load_artifact(stage))
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(stage),
        "source_body_sha256": hashlib.sha256(stage_frame.encoded_body).hexdigest(),
        "operations": [
            {
                "operation": "set_melodic_notes_from",
                "pattern": 1,
                "sound": 6,
                "keys": NOTES,
                "template_sound": 11,
            },
            {
                "operation": "set_drum_notes",
                "pattern": 1,
                "sound": 11,
                "keys": [None] * 16,
                "template_sound": 6,
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
    if melodic_notes(target, 1, 6) != NOTES or drum_notes(target, 1, 11) != [None] * 16:
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
                "observation_questions": [QUESTION],
                "hardware_restore": {"status": "not_run"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "long-melodic-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "sample": {
                    "path": sample_path.relative_to(root).as_posix(),
                    "sha256": sha256_file(sample_path),
                    "segment_hz": SEGMENT_HZ,
                    "segment_seconds": SEGMENT_SECONDS,
                },
                "allocation": allocation,
                "total_capacity_codes": TOTAL,
                "import_report_sha256": sha256_file(experiments / STAGE / "import-report.json"),
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/long_note_method.py"),
                "expected_duration_ms": EXPECTED_MS,
                "expected_quarter_hz": EXPECTED_HZ,
                "decision": [
                    "The backup must equal the compiled target exactly, every imported code included",
                    "whole_sample_plays holds when the five-loop median duration and at least 4 of 5 loops are within 10 ms of 2669.7 ms",
                    "quarters_in_order holds when every quarter's median and at least 4 of 5 loops are within 20 cents",
                ],
                "limits": [
                    "One 4.0 s sample in Sound6 at key 1 and pitch code 13; other lengths and slots follow by the same rule but are not played",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "total_codes": TOTAL}))


if __name__ == "__main__":
    main()
