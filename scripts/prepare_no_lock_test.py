"""Register the no-lock test: does code 0 keep the last locked filter or resonance value?

The resonance law test suggested that resonance code 0 is no parameter lock: each code-0
step sounded like the last step with a nonzero code (docs/resonance-law-results.md).
Volume code 0 behaved the same way, and filter code 0 measured flat right after a bypass
step. This test checks the rule for filter and resonance.

Source: the verified resonance-law state (Sound16 sawtooth on every step of Patterns
1..5). Through the public plan path the chain becomes 1, 2 and:
- Pattern1: resonance 1 on every step; filter FILTER_CODES, with zeros between locks and
  bypass references (63) on steps 1, 8 and 16.
- Pattern2: filter 16 on every step; resonance RESONANCE_CODES, with zeros between locks.

Models registered before the session (frozen filter-response method, five chain cycles):
- zero_holds_last_lock: every code-0 step's response is within 1 dB (median over
  harmonics of the absolute difference, median over cycles) of the most recent step of
  the same pattern with a nonzero code for that parameter.
- zero_filter_is_off: every filter code-0 step is within 1 dB of the bypass reference.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain
from po33_re.formats.notes import step_parameters
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact
from scripts.filter_response_method import SETTINGS
from scripts.prepare_resonance_law_test import DIRECTORY as SOURCE_EXPERIMENT

CHAIN = [1, 2]
FILTER_CODES = [63, 10, 0, 0, 50, 0, 0, 63, 0, 20, 0, 56, 0, 0, 0, 63]
RESONANCE_CODES = [1, 56, 0, 0, 8, 0, 0, 40, 0, 24, 0, 63, 0, 0, 1, 0]
PARAMETERS = {
    1: {"filter": FILTER_CODES, "resonance": [1] * 16},
    2: {"filter": [16] * 16, "resonance": RESONANCE_CODES},
}
PLAN_DIRECTORY = "no-lock-plan-001"
DIRECTORY = "compiled-no-lock-001"
REGISTRATION = "no-lock-registration-001.json"
PLAYBACK_SECONDS = 44
CYCLES = 5
QUESTION = "Did two alternating patterns play, with some steps repeating the sound before them? (Enter to skip)"


def step_plan():
    """For every step of one chain cycle: (pattern, step, filter, resonance)."""
    return [
        (p, s + 1, PARAMETERS[p]["filter"][s], PARAMETERS[p]["resonance"][s])
        for p in CHAIN
        for s in range(16)
    ]


def held_pairs():
    """(zero step index, last locked step index, parameter) within each pattern."""
    pairs = []
    plan = step_plan()
    for parameter, column in (("filter", 2), ("resonance", 3)):
        for n, row in enumerate(plan):
            if row[column] != 0:
                continue
            for m in range(n - 1, -1, -1):
                if plan[m][0] == row[0] and plan[m][column] != 0:
                    pairs.append((n, m, parameter))
                    break
    return pairs


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
        or not observation["checks"]["session_target_exact"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified resonance-law state is required")
    source = decode_artifact(load_artifact(source_path))
    operations = [
        {
            "operation": "set_step_parameters",
            "pattern": p,
            "sound": 16,
            "parameter": name,
            "values": values,
        }
        for p, params in PARAMETERS.items()
        for name, values in params.items()
    ]
    operations.append({"operation": "set_pattern_chain", "patterns": CHAIN})
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
    for p, params in PARAMETERS.items():
        steps = step_parameters(target, p, 16)
        for name, values in params.items():
            if [s[name] for s in steps] != values:
                raise ValueError(f"Pattern{p} {name} is not as planned")
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
                "analysis_version": "no-lock-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "parameters_by_pattern": {str(k): v for k, v in PARAMETERS.items()},
                "chain": CHAIN,
                "held_pairs": held_pairs(),
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/filter_response_method.py"),
                "cycles_measured": CYCLES,
                "hypotheses": {
                    "zero_holds_last_lock": "every code-0 step within 1 dB of the last nonzero step of the same pattern",
                    "zero_filter_is_off": "every filter code-0 step within 1 dB of the bypass reference",
                },
                "limits": [
                    "Filter and resonance on one drum sound; volume and pitch code 0 are not re-tested",
                    "Holding is checked within a pattern; the value at the start of a pattern is not",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "held_pairs": len(held_pairs())}))


if __name__ == "__main__":
    main()
