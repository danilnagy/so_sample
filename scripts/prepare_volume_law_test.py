"""Register a per-step volume law test through the public plan path.

From the verified pitch-law state, a hash-bound plan sets every Sound3 note in Pattern 1
to pitch 13 and gives each step its own volume code from 0 to 63. Earlier generated
restores measured volume 18 at 0.8189 and volume 36 at 2.2036 times volume 21. Two laws
fitted to those points are registered: amplitude proportional to code^1.38, and 0.5 dB per
code. Each is checked on every audible step within 1.5 dB; code 0 is reported only. The
measured gain table is the main result either way.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.notes import step_parameters
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_volume_gain_method import SETTINGS

SOURCE_EXPERIMENT = "compiled-pitch-law-002"
PLAN_DIRECTORY = "volume-law-plan-001"
DIRECTORY = "compiled-volume-law-001"
REGISTRATION = "volume-law-registration-001.json"
VOLUME_CODES = [36, 0, 63, 9, 54, 18, 45, 27, 3, 60, 12, 48, 21, 39, 6, 30]
PITCH = 13
PLAYBACK_SECONDS = 22
QUESTION = "Did the notes jump between loud and quiet, and did any distort? (Enter to skip)"
PRIOR_RATIOS = {"18_vs_21": 0.8189, "36_vs_21": 2.2036}
POWER = 1.38
DB_PER_CODE = 0.5


def power_db(code):
    if code == 0:
        return None
    return 20 * POWER * math.log10(code / VOLUME_CODES[0])


def linear_db(code):
    if code == 0:
        return None
    return DB_PER_CODE * (code - VOLUME_CODES[0])


MODELS = {
    "power_1p38": [power_db(c) for c in VOLUME_CODES],
    "db_linear_0p5": [linear_db(c) for c in VOLUME_CODES],
}


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    plan_folder = root / "experiments" / PLAN_DIRECTORY
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if plan_folder.exists() or folder.exists() or registration_path.exists():
        raise ValueError("Fresh plan folder, output folder and registration required")
    source_folder = root / "experiments" / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified pitch-law state is required")
    source_frame = decode_artifact(load_artifact(source_path))
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(source_path),
        "source_body_sha256": hashlib.sha256(source_frame.encoded_body).hexdigest(),
        "operations": [
            {
                "operation": "set_step_parameters",
                "pattern": 1,
                "sound": 3,
                "parameter": "pitch",
                "values": [PITCH] * 16,
            },
            {
                "operation": "set_step_parameters",
                "pattern": 1,
                "sound": 3,
                "parameter": "volume",
                "values": VOLUME_CODES,
            },
        ],
    }
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    report = compile_edit_plan(source_path, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    parameters = step_parameters(target, 1, 3)
    if [p["volume"] for p in parameters] != VOLUME_CODES or {p["pitch"] for p in parameters} != {
        PITCH
    }:
        raise ValueError("Compiled target does not hold the planned volume and pitch codes")
    before = step_parameters(source_frame, 1, 3)
    for old, new in zip(before, parameters):
        keep = ("filter", "resonance", "unknown_bit5")
        if any(old[k] != new[k] for k in keep):
            raise ValueError("A field other than pitch or volume changed")
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
                "analysis_version": "volume-law-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "plan": plan_path.relative_to(root).as_posix(),
                "plan_sha256": sha256_file(plan_path),
                "compile_report_sha256": sha256_file(folder / "compile-report.json"),
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": plan["source_artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "volume_codes": VOLUME_CODES,
                "pitch_code": PITCH,
                "prior_ratios": PRIOR_RATIOS,
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_volume_gain_method.py"
                ),
                "models_db": MODELS,
                "decision": [
                    "The backup must equal the compiled target exactly; only Pattern 1's Sound3 primary bytes may differ",
                    "Each step's level is the RMS 50-90 ms after its grid onset, median over five loops, in dB relative to step 1 (volume 36)",
                    "A model holds when every step with a nonzero code is within 1.5 dB in the median and in at least 4 of 5 loops",
                    "Code 0 is reported only; the measured gain table is the main result either way",
                ],
                "limits": [
                    "Sound3 at pitch 13 and key 1 on Pattern 1; other sounds may differ",
                    "Measures recorded output level, which includes the PO-33 and interface gain stages",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "codes": VOLUME_CODES}))


if __name__ == "__main__":
    main()
