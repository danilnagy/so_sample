"""Register a fresh F6/6F recording pair decided by the frozen step-1 pitch method.

The method (scripts/pattern1_fx_step_pitch_method.py) was developed on the -001
recordings, whose registered steady-tone comparison was inconclusive. This registration
freezes it, by file hash and settings, before the fresh -002 recordings. The restore
files are the -001 files, checked byte for byte against their earlier registration.
"""

import argparse
import json
import shutil
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from scripts.pattern1_fx_step_pitch_method import SETTINGS
from scripts.prepare_pattern1_fx_order_single_tone import QUESTION
from scripts.prepare_pattern1_fx_order_single_tone import REGISTRATION as FIRST_REGISTRATION

REGISTRATION = "pattern1-single-tone-FX-order-pitch-track-registration-001.json"
LEGS = {
    "a": {"directory": "edited-pattern1-single-tone-FX-F6-002", "previous": "a"},
    "b": {"directory": "edited-pattern1-single-tone-FX-6F-002", "previous": "b"},
}
PLAYBACK_SECONDS = 14
COPIED = ("edited.symbols.npz", "restore.wav", "redecoded.symbols.npz", "software-validation.json")


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    folders = {leg: root / "experiments" / spec["directory"] for leg, spec in LEGS.items()}
    if registration_path.exists() or any(f.exists() for f in folders.values()):
        raise ValueError("Fresh folders and registration required")
    first_path = root / "experiments" / FIRST_REGISTRATION
    first = json.loads(first_path.read_text())
    legs = {}
    for leg, folder in folders.items():
        previous = first["legs"][LEGS[leg]["previous"]]
        source = root / "experiments" / previous["directory"]
        if (
            sha256_file(source / "edited.symbols.npz") != previous["edited_artifact_sha256"]
            or sha256_file(source / "restore.wav") != previous["restore_wav_sha256"]
            or sha256_file(source / "software-validation.json")
            != previous["software_validation_sha256"]
        ):
            raise ValueError(f"Leg {leg}: earlier registered files changed")
        folder.mkdir()
        for name in COPIED:
            shutil.copyfile(source / name, folder / name)
        write_bytes(
            folder / "experiment.json",
            json_bytes(
                {
                    "experiment_id": folder.name,
                    "leg": leg,
                    "capture_status": "awaiting_hardware_session",
                    "restore_file": "restore.wav",
                    "expected_artifact": "edited.symbols.npz",
                    "registration": "../" + REGISTRATION,
                    "restore_copied_from": "../" + previous["directory"],
                    "playback_seconds": PLAYBACK_SECONDS,
                    "observation_questions": [QUESTION],
                    "hardware_restore": {"status": "not_run"},
                }
            ),
        )
        legs[leg] = {
            **previous,
            "directory": folder.name,
            "restore_copied_from": previous["directory"],
        }
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "single-tone-FX-order-pitch-track-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "method_developed_on": [first["legs"][k]["directory"] for k in ("a", "b")],
                "first_registration_sha256": sha256_file(first_path),
                "source_artifact": first["source_artifact"],
                "source_artifact_sha256": first["source_artifact_sha256"],
                "source_capture_sha256": first["source_capture_sha256"],
                "reference_frequency_hz": first["reference_frequency_hz"],
                "legs": legs,
                "capture_order": ["a", "b"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_fx_step_pitch_method.py"
                ),
                "predictions": {
                    "high_nibble_first": {"a_step1": "none", "b_step1": "effect"},
                    "low_nibble_first": {"a_step1": "effect", "b_step1": "none"},
                },
                "decision": [
                    "Both legs must be received exactly; only footer byte 0 may differ from the single-tone source",
                    "Step 1 (20-130 ms after onset, audible windows only) is 'effect' if the pitch reaches 10% above the 1190.417 Hz reference, 'none' if it stays within 1%, else indeterminate",
                    "A model is supported only if both legs' five-loop medians and at least 4 of 5 individual loops match its prediction",
                    "Anything else is inconclusive; no retuning after data",
                ],
                "limits": [
                    "Local to footer byte 0 of Pattern 1 with one Sound3 note on step 1",
                    "Characterizes where the rising effect sits, not its exact pitch law",
                    "No general per-step effect writer is enabled",
                ],
            }
        ),
    )
    for leg, folder in folders.items():
        write_bytes(
            folder / "instructions.md",
            (
                f"# Effect order confirmation, leg {leg.upper()}\n\n"
                "```powershell\n"
                f".\\.venv\\Scripts\\python.exe -m po33_re hw run experiments/{folder.name}\n"
                "```\n"
            ).encode(),
        )
    print(json.dumps({"ready": True, "legs": {k: f.name for k, f in folders.items()}}))


if __name__ == "__main__":
    main()
