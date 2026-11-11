"""Check the FX catalogue observation: reception, the control step, and a table per effect."""

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.fx_descriptor_method import SETTINGS, _prepare, describe
from scripts.prepare_fx_catalog_observation import (
    CHAIN,
    CONTROL,
    CYCLES,
    DIRECTORY,
    FX_OF_STEP,
    REGISTRATION,
    STEP_SECONDS,
    WINDOWS_MS,
)
from scripts.prepare_project_build_test import MELODY_KEY1_HZ

DECISION = "fx-catalog-decision-001.json"


def step_times(first, cycles):
    """Grid onset seconds of every described step, cycle by cycle, plus the control."""
    keys, times = [], []
    for cycle in range(cycles):
        base = first + cycle * len(CHAIN) * 16 * STEP_SECONDS
        for (pattern, step), fx in FX_OF_STEP.items():
            keys.append((cycle, fx))
            times.append(base + ((CHAIN.index(pattern) * 16) + step - 1) * STEP_SECONDS)
        keys.append((cycle, 0))
        times.append(base + ((CHAIN.index(CONTROL[0]) * 16) + CONTROL[1] - 1) * STEP_SECONDS)
    return keys, times


def cents(hz):
    return 1200 * math.log2(hz / MELODY_KEY1_HZ)


def control_plain(entry):
    sounding = [w for w in entry["windows"][:5] if w is not None and w["level_db"] > -30]
    following = [w for w in entry["windows"][6:] if w is not None]
    return (
        len(entry["onsets_ms"]) == 1
        and bool(sounding)
        and all(abs(cents(w["hz"])) <= 20 for w in sounding)
        and all(w["level_db"] <= -30 for w in following)
    )


def summarize(keys, described):
    """Median over cycles of each window's level and the dominant frequency as cents."""
    table = {}
    for fx in sorted({fx for _, fx in keys}):
        entries = [d for (_, f), d in zip(keys, described, strict=True) if f == fx]
        windows = []
        for i in range(len(WINDOWS_MS)):
            rows = [e["windows"][i] for e in entries if e["windows"][i] is not None]
            if not rows:
                windows.append(None)
                continue
            windows.append(
                {
                    "level_db": float(np.median([r["level_db"] for r in rows])),
                    "cents": float(np.median([cents(r["hz"]) for r in rows])),
                    "hz": float(np.median([r["hz"] for r in rows])),
                    "prominence_db": float(np.median([r["prominence_db"] for r in rows])),
                }
            )
        table[fx] = {
            "onset_counts": [len(e["onsets_ms"]) for e in entries],
            "onsets_ms": [e["onsets_ms"] for e in entries],
            "windows": windows,
            "control_plain_in_every_cycle": all(control_plain(e) for e in entries),
        }
    return table


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if sha256_file(root / "scripts/fx_descriptor_method.py") != registration[
        "method_script_sha256"
    ] or registration["windows_ms"] != [list(w) for w in WINDOWS_MS]:
        raise ValueError("Frozen method or windows changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "fx-catalog-measurements-001.json"
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
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "fx-catalog-native-check-0.1",
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
    _, _, _, first = _prepare(playback, SETTINGS)
    keys, times = step_times(first, CYCLES)
    control_index = keys.index((0, 0))
    described = describe(playback, times, WINDOWS_MS, control_index, SETTINGS)
    table = summarize(keys, described)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "fx-catalog-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "described_steps": [
                    {"cycle": c, "fx": fx, "onset_s": t, **d}
                    for (c, fx), t, d in zip(keys, times, described, strict=True)
                ],
            }
        ),
    )
    decision = {
        "analysis_version": "fx-catalog-decision-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": sha256_file(native_path),
        "measurements_sha256": sha256_file(measure_path),
        "hypotheses": {
            "exact_reception": checks["entire_actual_body_and_packets_match_target"],
            "control_plain": table[0]["control_plain_in_every_cycle"],
        },
        "effects": {str(fx): v for fx, v in table.items()},
        "limits": registration["limits"],
    }
    write_bytes(decision_path, json_bytes(decision))
    brief = {}
    for fx, v in table.items():
        levels = [None if w is None else round(w["level_db"]) for w in v["windows"]]
        pitches = [
            None if w is None or w["level_db"] < -30 else round(w["cents"]) for w in v["windows"]
        ]
        brief[fx] = {"onsets": v["onset_counts"], "level_db": levels, "cents": pitches}
    print(json.dumps({"hypotheses": decision["hypotheses"], "effects": brief}, indent=1))


if __name__ == "__main__":
    main()
