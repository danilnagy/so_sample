"""Register the resonance law test: every resonance code 0..63 at low-pass filter code 16.

Source: the verified filter-law state (Sound16 holds a 200 Hz sawtooth kit, Patterns 1..5
play it on every step, chain 1..5). Filter 16 is a low-pass with its -3 dB edge near
1400 Hz at resonance 0 (docs/filter-law-results.md). Through the public plan path, in
each pattern step 1 becomes the reference (filter 63 bypass, resonance 0) and steps 2..16
get filter 16 with the resonance codes in RESONANCE_CODES.

Hypotheses registered before the session (frozen method scripts/filter_response_method.py;
per resonance code the median response over its occurrences in two chain cycles):
- reference_consistent: every reference step within 0.5 dB of its cycle reference.
- peak_rises: the peak response over the 50 harmonics does not fall by more than 0.5 dB
  from one resonance code to the next.
- strong_at_63: the peak at resonance 63 is at least 10 dB above the peak at resonance 0.
- peak_near_edge: wherever the peak is at least +3 dB, it lies between 700 and 2800 Hz.
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
from scripts.prepare_filter_law_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_filter_law_test import PATTERNS

FILTER = 16
REFERENCE = (63, 0)
RESONANCE_CODES = {p: [0, *range(15 * (p - 1), 15 * (p - 1) + 15)] for p in (1, 2, 3, 4)} | {
    5: [0, 60, 61, 62, 63, 0, 16, 32, 48, 63, 8, 24, 40, 56, 31, 47]
}
PLAN_DIRECTORY = "resonance-law-plan-001"
DIRECTORY = "compiled-resonance-law-001"
REGISTRATION = "resonance-law-registration-001.json"
PLAYBACK_SECONDS = 44
QUESTION = "Did the tone get more ringing or whistling across the five patterns? (Enter to skip)"
PEAK_BAND_HZ = [700.0, 2800.0]


def step_layout():
    """(is_reference, resonance code) for every step of one chain cycle, in play order."""
    return [(step == 0, code) for p in PATTERNS for step, code in enumerate(RESONANCE_CODES[p])]


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
        raise ValueError("The verified filter-law state is required")
    source = decode_artifact(load_artifact(source_path))
    if pattern_chain(source) != PATTERNS:
        raise ValueError("The source chain must be 1..5")
    operations = []
    for p in PATTERNS:
        operations += [
            {
                "operation": "set_step_parameters",
                "pattern": p,
                "sound": 16,
                "parameter": "filter",
                "values": [REFERENCE[0]] + [FILTER] * 15,
            },
            {
                "operation": "set_step_parameters",
                "pattern": p,
                "sound": 16,
                "parameter": "resonance",
                "values": RESONANCE_CODES[p],
            },
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
    for p in PATTERNS:
        params = step_parameters(target, p, 16)
        if [(s["filter"], s["resonance"]) for s in params] != [REFERENCE] + [
            (FILTER, code) for code in RESONANCE_CODES[p][1:]
        ]:
            raise ValueError(f"Pattern{p} does not hold the planned parameters")
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
                "analysis_version": "resonance-law-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "filter_code": FILTER,
                "reference_filter_resonance": list(REFERENCE),
                "resonance_codes_by_pattern": {str(k): v for k, v in RESONANCE_CODES.items()},
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/filter_response_method.py"),
                "peak_band_hz": PEAK_BAND_HZ,
                "hypotheses": {
                    "reference_consistent": "every reference step within 0.5 dB of its cycle reference",
                    "peak_rises": "peak response never falls by more than 0.5 dB from one resonance code to the next",
                    "strong_at_63": "peak at resonance 63 at least 10 dB above the peak at resonance 0",
                    "peak_near_edge": "wherever the peak is at least +3 dB it lies between 700 and 2800 Hz",
                },
                "cycles_measured": 2,
                "limits": [
                    "One filter code (16, low-pass); resonance at high-pass codes is not measured",
                    "Responses are sampled at 200 Hz harmonics, so a narrow peak between harmonics is under-read",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
