"""Register the bit-5 glide test: does primary bit 5 switch off the pitch glide?

In the note bits test, notes with bit 5 set were 12.5 ms shorter than their plain
partners, but the plain partners followed a pitch change and the flagged ones did not, so
the glide into the new pitch may explain the difference (docs/note-bits-results.md).
Here every note follows a pitch change.

Source: the verified note-bits state (chain [2]; Sound1 on every step of Pattern2).
Through the public plan path, Pattern2's Sound1 notes alternate pitch codes 7 and 25, bit 5
clear on steps 1..8 and set on steps 9..16. At key 1 a pitch-25 note lasts 167 ms, within
a step, and a pitch-7 note 472 ms.

Frozen grid method, two readings per step: early, 20 ms windows at 5, 10 and 15 ms after
the onset, where a glide from the previous pitch still shows; late, at 100, 110 and
120 ms. Models, registered before the session, over the five-loop medians:
- bit5_inert: early and late readings, levels and pitch-25 durations of flagged steps
  match the plain steps of the same pitch within 20 cents, 1.5 dB and 5 ms.
- bit5_no_glide: flagged steps read within 20 cents of their target pitch early, while
  plain steps read at least 100 cents toward the previous pitch; flagged pitch-25 notes
  are shorter than plain ones by more than 5 ms.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain
from po33_re.formats.notes import step_parameters, unknown_bits
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact
from scripts.drum_slice_duration_method import SETTINGS as DURATION_SETTINGS
from scripts.pattern1_key_scale_grid_method import SETTINGS as GRID_SETTINGS
from scripts.polyphony_method_exploratory import SETTINGS as LEVEL_SETTINGS
from scripts.prepare_note_bits_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_note_bits_test import PATTERN
from scripts.prepare_polyphony_test import VOICES

PITCHES = [7 if step % 2 else 25 for step in range(1, 17)]
BITS = [0 if step <= 8 else 1 for step in range(1, 17)]
EARLY = {**GRID_SETTINGS, "window_starts_ms": [5.0, 10.0, 15.0]}
LATE = {**GRID_SETTINGS, "window_starts_ms": [100.0, 110.0, 120.0]}
BASE_HZ = VOICES[1]
EXPECTED_HZ = {step: BASE_HZ * 2 ** ((p - 13) / 12) for step, p in enumerate(PITCHES, 1)}
PLAN_DIRECTORY = "bit5-glide-plan-001"
DIRECTORY = "compiled-bit5-glide-001"
REGISTRATION = "bit5-glide-registration-001.json"
PLAYBACK_SECONDS = 22
QUESTION = "Did the second half of the pattern sound any different from the first? (Enter to skip)"
TOLERANCES = {"cents": 20.0, "db": 1.5, "ms": 5.0, "glide_cents": 100.0}


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
        or observation["reception"] != "exact"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified note-bits state is required")
    source = decode_artifact(load_artifact(source_path))
    if pattern_chain(source) != [PATTERN]:
        raise ValueError("The source chain must be [2]")
    operations = [
        {
            "operation": "set_step_parameters",
            "pattern": PATTERN,
            "sound": 1,
            "parameter": "pitch",
            "values": PITCHES,
        },
        {"operation": "set_note_unknown_bits", "pattern": PATTERN, "sound": 1, "values": BITS},
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
    if [p["pitch"] for p in step_parameters(target, PATTERN, 1)] != PITCHES or unknown_bits(
        target, PATTERN, 1
    ) != BITS:
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
                "analysis_version": "bit5-glide-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "pitches": PITCHES,
                "bits": BITS,
                "expected_hz": {str(k): v for k, v in EXPECTED_HZ.items()},
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "early_settings": EARLY,
                "late_settings": LATE,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "duration_method_settings": DURATION_SETTINGS,
                "duration_method_script_sha256": sha256_file(
                    root / "scripts/drum_slice_duration_method.py"
                ),
                "level_method_settings": LEVEL_SETTINGS,
                "level_method_script_sha256": sha256_file(
                    root / "scripts/polyphony_method_exploratory.py"
                ),
                "tolerances": TOLERANCES,
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "bit5_inert: flagged steps match plain steps of the same pitch in early and late pitch, level, and pitch-25 duration",
                    "bit5_no_glide: flagged steps start within 20 cents of target while plain steps start at least 100 cents toward the previous pitch, and flagged pitch-25 notes are more than 5 ms shorter",
                ],
                "limits": [
                    "One melodic sound at key 1 and two pitch codes; bit 5 on drum notes is not tested",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
