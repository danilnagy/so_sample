"""Check the stray bits observation: what the device kept, and what the even steps played."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.polyphony_method_exploratory import voice_levels
from scripts.prepare_stray_bits_test import (
    DIRECTORY,
    GLOBAL_BYTES,
    LEVEL_SETTINGS,
    ODD_STEPS,
    PATTERN,
    RAW_CELLS,
    REGISTRATION,
    VOICES,
)

DECISION = "stray-bits-decision-001.json"


def cell_outcomes(actual, target):
    data_a, data_t = pattern_data(actual, PATTERN), pattern_data(target, PATTERN)
    outcomes = {}
    for step, (sound, _, _) in RAW_CELLS.items():
        p, a = 48 * (step - 1) + 3 * (sound - 1), 768 + 16 * (step - 1) + sound - 1
        same = data_a[p : p + 3] == data_t[p : p + 3] and data_a[a] == data_t[a]
        empty = not any(data_a[p : p + 3]) and data_a[a] == 0
        outcomes[step] = {
            "sound": sound,
            "outcome": "kept" if same else ("cleared" if empty else "rewritten"),
            "actual_primary": data_a[p : p + 3].hex(),
            "actual_auxiliary": data_a[a],
        }
    return outcomes


def global_outcomes(actual, target):
    second_a = [p.payload for p in actual.packets if p.tag == 0x7D5C][1]
    second_t = [p.payload for p in target.packets if p.tag == 0x7D5C][1]
    return {
        str(offset): {
            "outcome": "kept" if second_a[offset] == second_t[offset] else "rewritten",
            "actual": second_a[offset],
        }
        for offset in GLOBAL_BYTES
    }


def other_differences(actual, target):
    """Pattern bytes outside the raw cells and global bytes outside 131..146 that differ."""
    count = 0
    for pattern in range(1, 17):
        a, t = pattern_data(actual, pattern), pattern_data(target, pattern)
        for i, (x, y) in enumerate(zip(a, t, strict=True)):
            if x == y:
                continue
            if pattern == PATTERN:
                raw = any(
                    i in range(48 * (s - 1) + 3 * (snd - 1), 48 * (s - 1) + 3 * snd)
                    or i == 768 + 16 * (s - 1) + snd - 1
                    for s, (snd, _, _) in RAW_CELLS.items()
                )
                if raw:
                    continue
            count += 1
    second_a = [p.payload for p in actual.packets if p.tag == 0x7D5C][1]
    second_t = [p.payload for p in target.packets if p.tag == 0x7D5C][1]
    count += sum(
        1
        for i, (x, y) in enumerate(zip(second_a, second_t, strict=True))
        if x != y and i not in GLOBAL_BYTES
    )
    return count


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / "scripts/polyphony_method_exploratory.py")
        != registration["level_method_script_sha256"]
        or registration["level_settings"] != LEVEL_SETTINGS
    ):
        raise ValueError("Frozen method or settings changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "stray-bits-measurements-001.json"
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
    cells = cell_outcomes(actual, target)
    globals_ = global_outcomes(actual, target)
    checks = {
        "native_valid": encode_packets(actual.packets) == actual.encoded_body,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": exact,
        "other_differences": other_differences(actual, target),
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "stray-bits-native-check-0.1",
        "hardware_verified": False,
        "passed": checks["native_valid"]
        and checks["target_body_matches_registration"]
        and checks["other_differences"] == 0
        and checks["capture_is_new"],
        "checks": checks,
        "raw_cells": {str(k): v for k, v in cells.items()},
        "global_bytes": globals_,
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": capture_hash,
        "artifact_sha256": sha256_file(artifact_path),
        "native_frame": frame_report(actual),
    }
    write_bytes(native_path, json_bytes(native))
    if not native["passed"]:
        print(json.dumps({"native": False, "checks": checks}, indent=2))
        raise ValueError("Native reception failed; report retained")
    names = list(VOICES)
    first, levels = voice_levels(playback, 16 * 5, [VOICES[n] for n in names], LEVEL_SETTINGS)
    db = 20 * np.log10(levels)
    reference = float(np.median([db[c * 16, 0] for c in range(5)]))
    steps = {}
    for step in range(1, 17):
        rows = [
            db[c * 16 + step - 1] for c in range(5) if not np.isnan(db[c * 16 + step - 1]).any()
        ]
        median = np.median(rows, axis=0) - reference
        steps[step] = {name: float(median[i]) for i, name in enumerate(names)}
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "stray-bits-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "first_onset_seconds": first,
                "reference_db": reference,
                "steps_db_vs_step1_sound8": {str(k): v for k, v in steps.items()},
            }
        ),
    )
    odd_ok = all(steps[s]["sound8_key1"] >= -10.0 for s in ODD_STEPS)
    even = {
        str(s): {name: round(v, 1) for name, v in steps[s].items() if v >= -10.0} for s in RAW_CELLS
    }
    decision = {
        "analysis_version": "stray-bits-decision-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": sha256_file(native_path),
        "measurements_sha256": sha256_file(measure_path),
        "hypotheses": {"raw_values_kept": exact, "odd_steps_normal": odd_ok},
        "raw_cells": {str(k): v for k, v in cells.items()},
        "global_bytes": globals_,
        "even_steps_sounding": even,
        "limits": registration["limits"],
    }
    write_bytes(decision_path, json_bytes(decision))
    print(
        json.dumps(
            {
                "native": True,
                "hypotheses": decision["hypotheses"],
                "raw_cells": {k: v["outcome"] for k, v in decision["raw_cells"].items()},
                "global_bytes_kept": all(v["outcome"] == "kept" for v in globals_.values()),
                "even_steps_sounding": even,
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
