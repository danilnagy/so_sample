"""Check the sample-memory limit test: exact reception of 241 pages, then Sound16."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.drum_import import drum_windows
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, sound_data
from po33_re.formats.patterns import drum_notes
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_memory_test import total_capacity
from scripts.drum_slice_duration_method import SETTINGS as DURATION_SETTINGS
from scripts.drum_slice_duration_method import decide as decide_durations
from scripts.drum_slice_duration_method import step_durations
from scripts.pattern1_key_scale_grid_method import decide, intervals, step_frequencies
from scripts.prepare_sample_memory_limit import (
    DIRECTORY,
    DURATION_MODEL_MS,
    KEYS,
    MODELS,
    REGISTRATION,
    SETTINGS,
    TOTAL,
    absolute_decision,
)

DECISION = "sample-memory-limit-decision-001.json"
OWNERS = {10: 24, 16: 120}
CAPACITIES = {10: 102400, 16: 69632}


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
        **{
            f"sound{slot}_buffer_matches_target": sound_data(actual, OWNERS[slot])
            == sound_data(target, OWNERS[slot])
            and len(sound_data(actual, OWNERS[slot])) == 9 + capacity
            for slot, capacity in CAPACITIES.items()
        },
        "total_capacity": total_capacity(actual) == TOTAL,
        "all_sound16_references": all(w is not None for w in drum_windows(actual, 16))
        and drum_windows(actual, 16) == drum_windows(target, 16),
        "planned_notes": drum_notes(actual, 1, 16) == KEYS
        and drum_notes(actual, 1, 9) == [None] * 16,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "sample-memory-limit-native-check-0.1",
        "hardware_verified": False,
        "passed": all(checks.values()),
        "checks": checks,
        "actual_total_capacity_codes": total_capacity(actual),
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
                "analysis_version": "sample-memory-limit-measurements-0.1",
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
                "analysis_version": "sample-memory-limit-decision-0.1",
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
                "total_codes": native["actual_total_capacity_codes"],
                "classification": decision["classification"],
                "cents": None
                if cents is None
                else {k: None if v is None else round(v, 1) for k, v in cents.items()},
                "absolute": absolute,
                "stops_at_window_end": duration["holds"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
