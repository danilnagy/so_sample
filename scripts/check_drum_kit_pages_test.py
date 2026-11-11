"""Check the page-capacity drum import test: exact reception, then Sound12 playback."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.drum_import import drum_ids, drum_windows
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, sound_data
from po33_re.formats.patterns import drum_notes
from po33_re.modem.symbols import load_artifact
from scripts.drum_slice_duration_method import SETTINGS as DURATION_SETTINGS
from scripts.drum_slice_duration_method import decide as decide_durations
from scripts.drum_slice_duration_method import step_durations
from scripts.pattern1_key_scale_grid_method import decide, intervals, step_frequencies
from scripts.prepare_drum_kit_pages_test import (
    CAPACITIES,
    DIRECTORY,
    DURATION_MODEL_MS,
    KEYS,
    MODELS,
    REGISTRATION,
    SETTINGS,
    absolute_decision,
)

DECISION = "drum-kit-pages-decision-001.json"


def kit_checks(actual, target):
    checks = {}
    for slot, capacity in CAPACITIES.items():
        owner = drum_ids(slot)[0]
        checks[f"sound{slot}_capacity_{capacity}"] = len(sound_data(actual, owner)) == 9 + capacity
        checks[f"sound{slot}_windows_match_target"] = drum_windows(actual, slot) == drum_windows(
            target, slot
        )
        checks[f"sound{slot}_codes_match_target"] = sound_data(actual, owner) == sound_data(
            target, owner
        )
    return checks


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    frozen = {
        "scripts/pattern1_key_scale_grid_method.py": registration["method_script_sha256"],
        "scripts/drum_slice_duration_method.py": registration["duration_method_script_sha256"],
    }
    if any(sha256_file(root / path) != pin for path, pin in frozen.items()):
        raise ValueError("A frozen method changed since registration")
    if (
        registration["method_settings"] != SETTINGS
        or registration["models_cents"] != MODELS
        or registration["duration_method_settings"] != DURATION_SETTINGS
        or registration["duration_model_ms"] != DURATION_MODEL_MS
    ):
        raise ValueError("Frozen settings or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "playback-measurements-001.json"
    decision_path = root / "experiments" / DECISION
    validate_outputs(
        [native_path, measure_path, decision_path],
        [capture, playback, artifact_path, target_path],
        False,
    )
    if sha256_file(target_path) != registration["edited_artifact_sha256"]:
        raise ValueError("Registered target changed")
    artifact = load_artifact(artifact_path)
    capture_hash = sha256_file(capture)
    if artifact.metadata["source_sha256"] != capture_hash:
        raise ValueError("Analysis artifact is not from capture.wav")
    target = decode_artifact(load_artifact(target_path))
    actual = decode_artifact(artifact)
    checks = {
        "native_valid": encode_packets(actual.packets) == actual.encoded_body,
        **kit_checks(actual, target),
        "planned_notes": drum_notes(actual, 1, 12) == KEYS
        and drum_notes(actual, 1, 11) == [None] * 16,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "drum-kit-pages-native-check-0.1",
        "hardware_verified": False,
        "passed": all(checks.values()),
        "checks": checks,
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": capture_hash,
        "artifact_sha256": sha256_file(artifact_path),
        "native_frame": frame_report(actual),
    }
    write_bytes(native_path, json_bytes(native))
    if not native["passed"]:
        print(json.dumps({"native": False, "checks": checks}, indent=2))
        raise ValueError("Native reception failed; report retained")
    info, steps = step_frequencies(playback, SETTINGS)
    table = intervals(steps)
    duration_info, durations = step_durations(playback, DURATION_SETTINGS)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "drum-kit-pages-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                **info,
                "step_frequencies_hz": {str(k): v for k, v in steps.items()},
                "intervals": None
                if table is None
                else {
                    "step1_hz": table["step1_hz"],
                    "steps": {str(k): v for k, v in table["steps"].items()},
                },
                "duration_settings": DURATION_SETTINGS,
                "duration_first_onset_seconds": duration_info["first_onset_seconds"],
                "step_durations_ms": {str(k): v for k, v in durations.items()},
            }
        ),
    )
    decision = decide(table, MODELS, SETTINGS)
    absolute = absolute_decision(None if table is None else table["step1_hz"])
    duration = decide_durations(durations, DURATION_MODEL_MS, DURATION_SETTINGS)
    cents = (
        None if table is None else {str(k): v["median_cents"] for k, v in table["steps"].items()}
    )
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "drum-kit-pages-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "measurements_sha256": sha256_file(measure_path),
                "step1_hz": None if table is None else table["step1_hz"],
                "measured_cents": cents,
                **decision,
                "absolute": absolute,
                "duration": {
                    "stops_at_window_end": duration["holds"],
                    "steps": {str(k): v for k, v in duration["steps"].items()},
                },
                "limits": registration["limits"],
            }
        ),
    )
    print(
        json.dumps(
            {
                "native": native["passed"],
                "classification": decision["classification"],
                "cents": None
                if cents is None
                else {k: None if v is None else round(v, 1) for k, v in cents.items()},
                "absolute": absolute,
                "stops_at_window_end": duration["holds"],
                "duration_ms": {
                    k: None if v["median_ms"] is None else round(v["median_ms"], 1)
                    for k, v in duration["steps"].items()
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
