"""Register the sample window test: is a nonzero start in a self-owned sample honoured?

Every melodic import so far started at code 0. Factory references (Sound3 into Sound1)
carry nonzero starts, but a nonzero start on a slot's own buffer is untested. Source: the
verified bit-5 glide state.

A 1.0 s sample of four 0.25 s segments at 400, 500, 600 and 700 Hz is imported into
Sound6 and Sound7 (page-rounded capacity). Then, through the public plan path:
- Sound6's header window becomes segment 3, Sound7's segment 2 (set_sample_window);
- Pattern2 plays Sound6 key 1 on steps 1, 5, 9, 13 and Sound7 on steps 3, 7, 11, 15, with
  Sound1's note parameters (pitch 13), and Sound1's notes are cleared. Chain stays [2].

At key 1 the device plays the stored audio 7 semitones up, so a 5859-code segment lasts
166.8 ms, within a step. Models, registered before the session (frozen grid method with
20 ms windows 100, 110 and 120 ms after the onset; frozen duration method):
- window_honoured: Sound6 plays segment 3 (600 Hz * 2^(7/12) = 899.0 Hz) and Sound7
  segment 2 (749.2 Hz), each 166.8 ms, within 20 cents and 5 ms.
- start_ignored: both play from code 0, so segment 1 (599.3 Hz) sounds in the window and
  the notes outlast the step (duration reads at least 230 ms).
If the device rewrites the headers, the backup differs from the target only in those 8
bytes per sound; that is classified window_rewritten_by_device.
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
from po33_re.formats.globals import pattern_chain
from po33_re.formats.packets import decode_artifact, sound_data
from po33_re.formats.patterns import melodic_notes
from po33_re.modem.symbols import load_artifact
from po33_re.sample_import import DEVICE_SAMPLE_LIMIT, compile_sample_import
from scripts.drum_slice_duration_method import SETTINGS as DURATION_SETTINGS
from scripts.pattern1_key_scale_grid_method import SETTINGS as GRID_SETTINGS
from scripts.prepare_bit5_glide_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_note_bits_test import PATTERN

SEGMENT_HZ = [400.0, 500.0, 600.0, 700.0]
SEGMENT_SECONDS, LEVEL, FADE_SECONDS, WAV_RATE = 0.25, 0.5, 0.002, 48000
NATIVE_RATE, TRANSPOSE = 23437.5, 2 ** (7 / 12)
NATIVE_CODES = 23438
BOUNDARIES = [round(NATIVE_RATE * SEGMENT_SECONDS * k) for k in range(5)]
WINDOWS = {6: (BOUNDARIES[2], BOUNDARIES[3]), 7: (BOUNDARIES[1], BOUNDARIES[2])}
SEGMENT_OF = {6: 3, 7: 2}
STEPS = {6: [1, 5, 9, 13], 7: [3, 7, 11, 15]}
EXPECTED_HZ = {slot: SEGMENT_HZ[SEGMENT_OF[slot] - 1] * TRANSPOSE for slot in WINDOWS}
IGNORED_HZ = SEGMENT_HZ[0] * TRANSPOSE
EXPECTED_MS = (BOUNDARIES[1] - BOUNDARIES[0]) / NATIVE_RATE / TRANSPOSE * 1000
SETTINGS = {**GRID_SETTINGS, "window_starts_ms": [100.0, 110.0, 120.0]}
TOLERANCES = {"cents": 20.0, "ms": 5.0, "long_ms": 230.0}
SAMPLE_DIRECTORY = "sample-window-source-001"
STAGES = {6: "import-sound6-window-stage-001", 7: "import-sound7-window-stage-001"}
PLAN_DIRECTORY = "sample-window-plan-001"
DIRECTORY = "compiled-sample-window-001"
REGISTRATION = "sample-window-registration-001.json"
PLAYBACK_SECONDS = 22
QUESTION = "Did the notes alternate between two short tones, or sound like the same rising sample? (Enter to skip)"


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


def keys_for(slot):
    return [1 if step in STEPS[slot] else None for step in range(1, 17)]


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    names = [SAMPLE_DIRECTORY, PLAN_DIRECTORY, DIRECTORY, *STAGES.values()]
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any((experiments / name).exists() for name in names):
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
        raise ValueError("The verified bit-5 glide state is required")
    sample_folder = experiments / SAMPLE_DIRECTORY
    sample_folder.mkdir()
    sample_path = sample_folder / "four-segments-400-700hz-1s.wav"
    write_bytes(sample_path, sample_wav())
    current, imports = source_path, {}
    for slot, stage in STAGES.items():
        imports[slot] = compile_sample_import(
            current,
            sample_path,
            experiments / stage,
            slot,
            None,
            None,
            (slot,),
            DEVICE_SAMPLE_LIMIT,
            max_frames=NATIVE_CODES,
            page_capacity=True,
        )
        if imports[slot]["allocation"]["endpoint"] != NATIVE_CODES:
            raise ValueError(f"Sound{slot} import did not keep the planned length")
        current = experiments / stage / "edited.symbols.npz"
    stage_frame = decode_artifact(load_artifact(current))
    if pattern_chain(stage_frame) != [PATTERN]:
        raise ValueError("The source chain must be [2]")
    operations = [
        {
            "operation": "set_step_parameters",
            "pattern": PATTERN,
            "sound": 1,
            "parameter": "pitch",
            "values": [13] * 16,
        },
        {"operation": "set_note_unknown_bits", "pattern": PATTERN, "sound": 1, "values": [0] * 16},
        *(
            {"operation": "set_sample_window", "sound": slot, "start": start, "end": end}
            for slot, (start, end) in WINDOWS.items()
        ),
        *(
            {
                "operation": "set_melodic_notes_from",
                "pattern": PATTERN,
                "sound": slot,
                "keys": keys_for(slot),
                "template_sound": 1,
            }
            for slot in WINDOWS
        ),
        {"operation": "set_melodic_notes", "pattern": PATTERN, "sound": 1, "keys": [None] * 16},
    ]
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
    for slot, (start, end) in WINDOWS.items():
        header = sound_data(target, slot - 1)[:9]
        if (
            int.from_bytes(header[:4], "little") != start
            or int.from_bytes(header[4:8], "little") != end
            or melodic_notes(target, PATTERN, slot) != keys_for(slot)
        ):
            raise ValueError(f"Sound{slot} window or notes are not as planned")
    if melodic_notes(target, PATTERN, 1) != [None] * 16:
        raise ValueError("Sound1 notes were not cleared")
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
                "observation_questions": [QUESTION],
                "hardware_restore": {"status": "not_run"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "sample-window-registration-0.1",
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
                    "native_codes": NATIVE_CODES,
                },
                "boundaries_codes": BOUNDARIES,
                "windows": {str(k): list(v) for k, v in WINDOWS.items()},
                "steps": {str(k): v for k, v in STEPS.items()},
                "expected_hz": {str(k): v for k, v in EXPECTED_HZ.items()},
                "ignored_hz": IGNORED_HZ,
                "expected_ms": EXPECTED_MS,
                "import_reports_sha256": {
                    str(slot): sha256_file(experiments / stage / "import-report.json")
                    for slot, stage in STAGES.items()
                },
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
                "tolerances": TOLERANCES,
                "decision": [
                    "Reception: the backup equals the target exactly, or differs only in the two 8-byte windows (window_rewritten_by_device)",
                    "window_honoured: every note within 20 cents of its segment's frequency and within 5 ms of 166.8 ms, in the five-loop median",
                    "start_ignored: every note within 20 cents of segment 1's frequency and at least 230 ms long",
                ],
                "limits": [
                    "Two windows at segment boundaries in one sample; sub-segment offsets and references are not tested",
                ],
            }
        ),
    )
    print(
        json.dumps(
            {"ready": True, "folder": DIRECTORY, "windows": WINDOWS, "expected_ms": EXPECTED_MS}
        )
    )


if __name__ == "__main__":
    main()
