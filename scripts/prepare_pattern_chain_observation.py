"""Register a device-side observation: chain Patterns 1 and 5, then back up and play.

The verified selected-pattern restore is played first, so the device starts from a known
state: Pattern1 plays eight rising tones, Pattern5 the same tones falling, and Pattern5 is
selected. The person then chains Pattern1 then Pattern5 on the device, takes a backup
and records playback.

Hypotheses registered before the backup:
- chain_in_global_record_only: every changed byte is in the 0x7d5c global records; no
  pattern or sound record changes.
- Playback, per loop, against absolute step frequencies (frozen grid method): chain_1_5
  plays Pattern1 then Pattern5 alternately from the first loop; chain_5_1 plays Pattern5
  then Pattern1. A model holds when at least 4 of 5 loops match it on all 16 steps
  within 20 cents.
"""

import argparse
import json
import shutil
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from scripts.prepare_all_melodic_slots_test import SETTINGS, TONE_HZ
from scripts.prepare_selected_pattern_test import DIRECTORY as SOURCE_EXPERIMENT

DIRECTORY = "observe-pattern-chain-001"
REGISTRATION = "pattern-chain-registration-001.json"
TRANSPOSE = 2 ** (7 / 12)
PATTERN1_HZ = [TONE_HZ[(step + 1) // 2] * TRANSPOSE for step in range(1, 17)]
PATTERN5_HZ = [TONE_HZ[9 - (step + 1) // 2] * TRANSPOSE for step in range(1, 17)]
MODELS = {
    "chain_1_5": [PATTERN1_HZ, PATTERN5_HZ, PATTERN1_HZ, PATTERN5_HZ, PATTERN1_HZ],
    "chain_5_1": [PATTERN5_HZ, PATTERN1_HZ, PATTERN5_HZ, PATTERN1_HZ, PATTERN5_HZ],
}
PLAYBACK_SECONDS = 26
QUESTIONS = [
    "How did you make the chain, and what did the screen show? (Enter to skip)",
    "Did playback alternate between rising and falling runs? Which came first? (Enter to skip)",
]
INSTRUCTIONS = """Chain Pattern 1 then Pattern 5 on the PO-33:

1. Hold PATTERN.
2. While holding it, press key 1, then key 5.
3. Release PATTERN.

Do not press play or any other key before the backup. The harness records playback after
the backup; press play only when it asks."""


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    folder = experiments / DIRECTORY
    registration_path = experiments / REGISTRATION
    if folder.exists() or registration_path.exists():
        raise ValueError("Fresh folder and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    if not observation["hardware_verified"] or observation["classification"] != (
        "pattern5_selected"
    ):
        raise ValueError("The verified selected-pattern state is required")
    source_registration = json.loads(
        (experiments / "selected-pattern-registration-001.json").read_text()
    )
    restore = source_folder / "restore.wav"
    target = source_folder / "edited.symbols.npz"
    if (
        sha256_file(restore) != source_registration["restore_wav_sha256"]
        or sha256_file(target) != source_registration["edited_artifact_sha256"]
    ):
        raise ValueError("The verified restore or its target changed")
    folder.mkdir()
    shutil.copyfile(restore, folder / "restore.wav")
    write_bytes(folder / "instructions.md", INSTRUCTIONS.encode())
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "kind": "device_side_observation_after_restore",
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "source_artifact": "../" + SOURCE_EXPERIMENT + "/edited.symbols.npz",
                "registration": "../" + REGISTRATION,
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
                "analysis_version": "pattern-chain-registration-0.1",
                "hardware_verified": False,
                "registered_before_backup": True,
                "experiment_id": DIRECTORY,
                "restore_wav_sha256": sha256_file(folder / "restore.wav"),
                "baseline_artifact": target.relative_to(root).as_posix(),
                "baseline_artifact_sha256": sha256_file(target),
                "instructions": INSTRUCTIONS,
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_hz_by_loop": MODELS,
                "hypotheses": {
                    "chain_in_global_record_only": "only 0x7d5c record bytes change against the restored target",
                    "chain_1_5": "loops alternate Pattern1, Pattern5 from the first loop",
                    "chain_5_1": "loops alternate Pattern5, Pattern1 from the first loop",
                },
                "decision": [
                    "Structure: every byte that differs from the restored target lies in a 0x7d5c record",
                    "Playback: a model holds when at least 4 of 5 loops have all 16 steps within 20 cents of its frequencies",
                ],
                "limits": [
                    "One chain of two patterns made one way; longer chains and chain editing are not tested",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
