"""Register the chain writer test: write the chain 5, 1, 1 through the plan path.

Source: the verified selected-pattern state (Pattern1 rises, Pattern5 falls, chain [5]).
The plan sets the chain to [5, 1, 1]: entries 4, 0, 0 in bytes 0..2 of the second global
record and length 3 in byte 128. The person presses only play.

Models of the five measured loops, each against absolute step frequencies:
- chain_5_1_1: Pattern5, Pattern1, Pattern1, Pattern5, Pattern1.
- first_entry_only: Pattern5 on every loop.
- two_entries_alternate: Pattern5, Pattern1, Pattern5, Pattern1, Pattern5.
A model holds when at least 4 of 5 loops match it on all 16 steps within 20 cents.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact
from scripts.prepare_pattern_chain_observation import PATTERN1_HZ, PATTERN5_HZ, SETTINGS
from scripts.prepare_selected_pattern_test import DIRECTORY as SOURCE_EXPERIMENT

CHAIN = [5, 1, 1]
PLAN_DIRECTORY = "chain-writer-plan-001"
DIRECTORY = "compiled-chain-writer-001"
REGISTRATION = "chain-writer-registration-001.json"
PLAYBACK_SECONDS = 26
QUESTION = "Did playback go falling, rising, rising, then repeat? (Enter to skip)"
P1, P5 = PATTERN1_HZ, PATTERN5_HZ
MODELS = {
    "chain_5_1_1": [P5, P1, P1, P5, P1],
    "first_entry_only": [P5, P5, P5, P5, P5],
    "two_entries_alternate": [P5, P1, P5, P1, P5],
}


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
        or observation["classification"] != "pattern5_selected"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified selected-pattern state is required")
    source = decode_artifact(load_artifact(source_path))
    if pattern_chain(source) != [5]:
        raise ValueError("The source chain must be [5]")
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(source_path),
        "source_body_sha256": hashlib.sha256(source.encoded_body).hexdigest(),
        "operations": [{"operation": "set_pattern_chain", "patterns": CHAIN}],
    }
    plan_folder = experiments / PLAN_DIRECTORY
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    folder = experiments / DIRECTORY
    report = compile_edit_plan(source_path, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    if pattern_chain(target) != CHAIN:
        raise ValueError("Compiled target does not hold the planned chain")
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
                "analysis_version": "chain-writer-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "chain": CHAIN,
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_hz_by_loop": MODELS,
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "A model holds when at least 4 of 5 loops match it on all 16 steps within 20 cents",
                ],
                "limits": [
                    "One three-entry chain with a repeated pattern; longer chains are not played",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
