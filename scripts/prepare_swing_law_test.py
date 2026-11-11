"""Register the swing law test at swing 18: how far are even steps delayed?

Known: the swing byte (second global record, byte 130) shows 0..18 on the device; a
generated swing 6 at 137 BPM delayed the even steps by 27.2 ms, 0.124 of the two-step
interval, so the even step sat at position 0.624 instead of 0.5
(docs/generated-swing6-results.md). The scale is unknown.

Source: the verified sample-window state. Through the public plan path, Sound6's window
becomes a 2000-code click (57 ms at key 1), Sound6 plays on every step of Pattern2,
Sound7's notes are cleared, and the swing byte becomes 18. Tempo stays 60 BPM.

Models of the even-step position, registered before the session (frozen method
scripts/swing_onset_method.py, five loops, median):
- linear_in_code: 0.5 + 18 * (0.124 / 6) = 0.872.
- triplet_at_max: 0.667, the classic maximum swing.
- three_quarters_at_max: 0.75.
A model holds when the median position is within 0.02 of it and the spread over all even
steps and loops is below 0.04. Odd steps are assumed on the grid; the whole-loop length
is reported.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain, swing
from po33_re.formats.packets import decode_artifact, sound_data
from po33_re.formats.patterns import melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.prepare_note_bits_test import PATTERN
from scripts.prepare_sample_window_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_sample_window_test import WINDOWS
from scripts.swing_onset_method import SETTINGS

SWING = 18
CLICK_CODES = 2000
CLICK_WINDOW = (WINDOWS[6][0], WINDOWS[6][0] + CLICK_CODES)
SWING6_POSITION = 0.5 + 27.2 / 219.0
MODELS = {
    "linear_in_code": 0.5 + SWING * ((SWING6_POSITION - 0.5) / 6),
    "triplet_at_max": 2 / 3,
    "three_quarters_at_max": 0.75,
}
TOLERANCE, MAX_SPREAD = 0.02, 0.04
PLAN_DIRECTORY = "swing-law-plan-001"
DIRECTORY = "compiled-swing-law-001"
REGISTRATION = "swing-law-registration-001.json"
PLAYBACK_SECONDS = 22
QUESTION = "Did the clicks sound strongly swung, almost in pairs? What did the swing display show? (Enter to skip)"


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
        or observation["classification"] != "window_honoured"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified sample-window state is required")
    source = decode_artifact(load_artifact(source_path))
    if pattern_chain(source) != [PATTERN] or swing(source) != 0:
        raise ValueError("The source must play Pattern2 alone with swing 0")
    operations = [
        {
            "operation": "set_sample_window",
            "sound": 6,
            "start": CLICK_WINDOW[0],
            "end": CLICK_WINDOW[1],
        },
        {"operation": "set_melodic_notes", "pattern": PATTERN, "sound": 6, "keys": [1] * 16},
        {"operation": "set_melodic_notes", "pattern": PATTERN, "sound": 7, "keys": [None] * 16},
        {"operation": "set_swing_byte", "value": SWING},
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
    header = sound_data(target, 5)[:9]
    if (
        (int.from_bytes(header[:4], "little"), int.from_bytes(header[4:8], "little"))
        != CLICK_WINDOW
        or melodic_notes(target, PATTERN, 6) != [1] * 16
        or melodic_notes(target, PATTERN, 7) != [None] * 16
        or swing(target) != SWING
    ):
        raise ValueError("Compiled target is not as planned")
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
                "analysis_version": "swing-law-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "swing": SWING,
                "click_window": list(CLICK_WINDOW),
                "swing6_reference_position": SWING6_POSITION,
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/swing_onset_method.py"),
                "models_position": MODELS,
                "tolerance": TOLERANCE,
                "max_spread": MAX_SPREAD,
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "A model holds when the five-loop median even-step position is within 0.02 of it and the spread is below 0.04",
                ],
                "limits": [
                    "One swing value at 60 BPM; the law between 6 and 18 is interpolated, not measured",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "models": MODELS}))


if __name__ == "__main__":
    main()
