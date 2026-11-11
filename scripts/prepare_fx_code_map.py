"""Register a device-side effect code map: FX key N recorded into pattern N+1.

The device starts from the verified position-map state, where patterns 2..16 are empty
with clear footers. The person records each FX key 1..15 into its own pattern; one
backup then shows which footer code each key stores. Keys 7 and 8 have known codes
(6 and 7) and act as controls. Prediction, registered before the backup: code = key - 1.
"""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact

DIRECTORY = "observe-FX-code-map-001"
REGISTRATION = "FX-code-map-registration-001.json"
BASELINE_EXPERIMENT = "edited-pattern1-FX-position-map-001"
BASELINE = BASELINE_EXPERIMENT + "/derived/analysis-001/capture.symbols.npz"
KEYS = list(range(1, 16))

INSTRUCTIONS = """# Effect code map

The PO-33 should still hold the position-map state from the last session (pattern 1
with four notes, patterns 2 to 16 empty). For each FX key N from 1 to 15, record it
into pattern N+1:

1. Select pattern N+1: hold PATTERN and press key N+1.
2. Press WRITE to turn write mode on, then PLAY.
3. Hold FX and key N together for about 5 seconds (two loops).
4. Release, press PLAY to stop, and press WRITE to turn write mode off.

So key 1 goes into pattern 2, key 2 into pattern 3, and so on up to key 15 into
pattern 16. Do not touch pattern 1, the knobs, the tempo or the sounds. Note any key
that seems to do nothing or behaves oddly. When all 15 are done, press Enter here to
take the backup.
"""


def pattern_for_key(key):
    return key + 1


def predicted_code(key):
    return key - 1


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if folder.exists() or registration_path.exists():
        raise ValueError("Fresh folder and registration required")
    baseline_path = root / "experiments" / BASELINE
    baseline_folder = root / "experiments" / BASELINE_EXPERIMENT
    observation = json.loads((baseline_folder / "hardware-observation-001.json").read_text())
    native = json.loads((baseline_folder / "hardware-recapture-results-001.json").read_text())
    if (
        not observation["hardware_verified"]
        or sha256_file(baseline_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified position-map state is required")
    frame = decode_artifact(load_artifact(baseline_path))
    for key in KEYS:
        data = pattern_data(frame, pattern_for_key(key))
        if any(data[:1024]) or data[1024:] != bytes([0xFF]) * 8:
            raise ValueError(f"Pattern {pattern_for_key(key)} must be empty with clear effects")
    folder.mkdir()
    write_bytes(folder / "instructions.md", INSTRUCTIONS.encode())
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "kind": "device_side_observation",
                "capture_status": "awaiting_hardware_session",
                "source_artifact": "../" + BASELINE,
                "registration": "../" + REGISTRATION,
                "observation_questions": [
                    "Did any FX key seem to do nothing or behave oddly? (Enter to skip)"
                ],
                "hardware_restore": {"status": "not_applicable"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "FX-code-map-registration-0.1",
                "hardware_verified": False,
                "registered_before_backup": True,
                "experiment_id": DIRECTORY,
                "baseline_artifact": "experiments/" + BASELINE,
                "baseline_artifact_sha256": sha256_file(baseline_path),
                "baseline_body_sha256": native["native_frame"]["encoded_body_sha256"],
                "assignments": {str(k): pattern_for_key(k) for k in KEYS},
                "predicted_codes": {str(k): f"{predicted_code(k):X}" for k in KEYS},
                "known_controls": {"7": "6", "8": "7"},
                "decision": [
                    "For each key, the codes stored in its pattern's footer are read; F means no effect",
                    "A key maps to a code when its pattern holds exactly one non-F code",
                    "The key-minus-one model is supported when all 15 keys map to their predicted codes and both controls match",
                    "Other changes outside the footers of patterns 2..16 are reported, not interpreted",
                ],
                "limits": [
                    "Records codes only; what each effect sounds like is not measured",
                    "Coverage depends on how long each key was held",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
