"""Check the sample window test: reception (allowing rewritten windows), pitch, duration."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, sound_data
from po33_re.modem.symbols import load_artifact
from scripts.drum_slice_duration_method import SETTINGS as DURATION_SETTINGS
from scripts.drum_slice_duration_method import step_durations
from scripts.pattern1_key_scale_grid_method import step_frequencies
from scripts.prepare_sample_window_test import (
    DIRECTORY,
    EXPECTED_HZ,
    EXPECTED_MS,
    IGNORED_HZ,
    REGISTRATION,
    SETTINGS,
    STEPS,
    TOLERANCES,
    WINDOWS,
)

DECISION = "sample-window-decision-001.json"


def windows_only_difference(actual, target):
    """True when the frames differ only in the first 8 header bytes of Sound6 and Sound7."""
    if actual.packets == target.packets:
        return False

    def stripped(frame):
        out = []
        for sid in range(136):
            try:
                data = sound_data(frame, sid)
            except ValueError:
                data = b""
            out.append(data[8:] if sid + 1 in WINDOWS else data)
        out.extend(p for p in frame.packets if p.tag != 0xEF78)
        return out

    return stripped(actual) == stripped(target)


def cents(values, hz):
    usable = [f for f in values if f is not None]
    return None if not usable else float(1200 * np.log2(np.median(usable) / hz))


def evaluate(steps, durations):
    notes = {}
    for slot, slot_steps in STEPS.items():
        for step in slot_steps:
            notes[step] = {
                "sound": slot,
                "cents_from_window": cents(steps.get(step, []), EXPECTED_HZ[slot]),
                "cents_from_segment1": cents(steps.get(step, []), IGNORED_HZ),
                "duration_ms": float(np.median(durations[step])),
            }
    honoured = all(
        n["cents_from_window"] is not None
        and abs(n["cents_from_window"]) <= TOLERANCES["cents"]
        and abs(n["duration_ms"] - EXPECTED_MS) <= TOLERANCES["ms"]
        for n in notes.values()
    )
    ignored = all(
        n["cents_from_segment1"] is not None
        and abs(n["cents_from_segment1"]) <= TOLERANCES["cents"]
        and n["duration_ms"] >= TOLERANCES["long_ms"]
        for n in notes.values()
    )
    support = {"window_honoured": honoured, "start_ignored": ignored}
    holding = [m for m, ok in support.items() if ok]
    return {
        "notes": {str(k): v for k, v in notes.items()},
        "model_support": support,
        "classification": holding[0] if len(holding) == 1 else "other_or_inconclusive",
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    pins = {
        "scripts/pattern1_key_scale_grid_method.py": registration["method_script_sha256"],
        "scripts/drum_slice_duration_method.py": registration["duration_method_script_sha256"],
    }
    if any(sha256_file(root / path) != pin for path, pin in pins.items()):
        raise ValueError("A frozen method changed since registration")
    if registration["method_settings"] != SETTINGS or registration["tolerances"] != TOLERANCES:
        raise ValueError("Frozen settings changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "sample-window-measurements-001.json"
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
    exact = actual.packets == target.packets and actual.encoded_body == target.encoded_body
    rewritten = windows_only_difference(actual, target)
    checks = {
        "native_valid": encode_packets(actual.packets) == actual.encoded_body,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": exact,
        "differs_only_in_windows": rewritten,
        "reception_accepted": exact or rewritten,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    actual_windows = {
        str(slot): [
            int.from_bytes(sound_data(actual, slot - 1)[:4], "little"),
            int.from_bytes(sound_data(actual, slot - 1)[4:8], "little"),
        ]
        for slot in WINDOWS
    }
    native = {
        "analysis_version": "sample-window-native-check-0.1",
        "hardware_verified": False,
        "passed": checks["native_valid"]
        and checks["target_body_matches_registration"]
        and checks["reception_accepted"]
        and checks["capture_is_new"],
        "checks": checks,
        "actual_windows": actual_windows,
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
    _, durations = step_durations(playback, DURATION_SETTINGS)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "sample-window-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                **info,
                "step_frequencies_hz": {str(k): v for k, v in steps.items()},
                "step_durations_ms": {str(k): v for k, v in durations.items()},
            }
        ),
    )
    result = evaluate(steps, durations)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "sample-window-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "measurements_sha256": sha256_file(measure_path),
                "reception": "exact" if exact else "window_rewritten_by_device",
                "actual_windows": actual_windows,
                **result,
                "limits": registration["limits"],
            }
        ),
    )
    print(
        json.dumps(
            {
                "native": True,
                "reception": "exact" if exact else "window_rewritten_by_device",
                "classification": result["classification"],
                "notes": {
                    k: [
                        v["sound"],
                        None
                        if v["cents_from_window"] is None
                        else round(v["cents_from_window"], 1),
                        round(v["duration_ms"], 1),
                    ]
                    for k, v in result["notes"].items()
                },
            }
        )
    )


if __name__ == "__main__":
    main()
