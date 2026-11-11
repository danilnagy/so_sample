"""Check the note bits test: reception (allowing a cleared bit 5), pitch models, bit-5 pairs."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.notes import unknown_bits
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.drum_slice_duration_method import SETTINGS as DURATION_SETTINGS
from scripts.drum_slice_duration_method import step_durations
from scripts.pattern1_key_scale_grid_method import decide, intervals, step_frequencies
from scripts.polyphony_method_exploratory import SETTINGS as LEVEL_SETTINGS
from scripts.polyphony_method_exploratory import voice_levels
from scripts.prepare_note_bits_test import (
    BIT5_PAIRS,
    DIRECTORY,
    DURATION_PAIRS,
    EXPECTED_HZ,
    MODELS,
    PATTERN,
    REGISTRATION,
    SETTINGS,
    STEPS,
)

DECISION = "note-bits-decision-001.json"
TOLERANCES = {"cents": 20.0, "db": 1.5, "ms": 5.0}


def bit5_only_difference(actual, target):
    """True when the two frames differ only in bit 5 of the flagged Sound1 cells."""
    if actual.packets == target.packets:
        return False
    stripped_a, stripped_t = [], []
    for frame, out in ((actual, stripped_a), (target, stripped_t)):
        data = bytearray(pattern_data(frame, PATTERN))
        for step, (_, flag) in STEPS.items():
            if flag:
                offset = 48 * (step - 1)
                data[offset] &= ~(1 << 5)
        out.append(bytes(data))
        out.extend(pattern_data(frame, p) for p in range(1, 17) if p != PATTERN)
        out.extend(p for p in frame.packets if p.tag not in (0xC498, 0xA041))
    return stripped_a == stripped_t


def bit5_comparisons(table, levels_db, durations):
    rows = []
    for flagged, plain in BIT5_PAIRS:
        cents = table["steps"][flagged]["median_cents"] - table["steps"][plain]["median_cents"]
        db = levels_db[flagged] - levels_db[plain]
        row = {"flagged_step": flagged, "plain_step": plain, "cents_diff": cents, "db_diff": db}
        if (flagged, plain) in DURATION_PAIRS:
            row["ms_diff"] = float(np.median(durations[flagged]) - np.median(durations[plain]))
        rows.append(row)
    inert = all(
        abs(r["cents_diff"]) <= TOLERANCES["cents"]
        and abs(r["db_diff"]) <= TOLERANCES["db"]
        and abs(r.get("ms_diff", 0.0)) <= TOLERANCES["ms"]
        for r in rows
    )
    return rows, inert


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    pins = {
        "scripts/pattern1_key_scale_grid_method.py": registration["method_script_sha256"],
        "scripts/drum_slice_duration_method.py": registration["duration_method_script_sha256"],
        "scripts/polyphony_method_exploratory.py": registration["level_method_script_sha256"],
    }
    if any(sha256_file(root / path) != pin for path, pin in pins.items()):
        raise ValueError("A frozen method changed since registration")
    if registration["method_settings"] != SETTINGS or registration["models_cents"] != MODELS:
        raise ValueError("Frozen settings or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "note-bits-measurements-001.json"
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
    bit5_cleared = bit5_only_difference(actual, target)
    checks = {
        "native_valid": encode_packets(actual.packets) == actual.encoded_body,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": exact,
        "differs_only_in_bit5": bit5_cleared,
        "reception_accepted": exact or bit5_cleared,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "note-bits-native-check-0.1",
        "hardware_verified": False,
        "passed": checks["native_valid"]
        and checks["target_body_matches_registration"]
        and checks["reception_accepted"]
        and checks["capture_is_new"],
        "checks": checks,
        "bit5_stored": None if not checks["reception_accepted"] else exact,
        "actual_bit5": unknown_bits(actual, PATTERN, 1),
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
    frequencies = sorted(set(EXPECTED_HZ.values()))
    _, levels = voice_levels(playback, 16 * SETTINGS["loops"], frequencies, LEVEL_SETTINGS)
    levels_db = {}
    for step, hz in EXPECTED_HZ.items():
        column = frequencies.index(hz)
        values = [levels[c * 16 + step - 1, column] for c in range(SETTINGS["loops"])]
        levels_db[step] = float(20 * np.log10(np.median(values)))
    _, durations = step_durations(playback, DURATION_SETTINGS)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "note-bits-measurements-0.1",
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
                "levels_db": {str(k): v for k, v in levels_db.items()},
                "step_durations_ms": {str(k): v for k, v in durations.items()},
            }
        ),
    )
    decision = decide(table, MODELS, SETTINGS) if table else None
    pitch = {
        "model_support": None if decision is None else decision["model_support"],
        "classification": None if decision is None else decision["classification"],
    }
    rows, inert = bit5_comparisons(table, levels_db, durations)
    result = {
        "analysis_version": "note-bits-decision-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": sha256_file(native_path),
        "measurements_sha256": sha256_file(measure_path),
        "bit5_stored": native["bit5_stored"],
        "reception": "exact" if exact else "bit5_cleared_by_device",
        "measured_cents": None
        if table is None
        else {str(k): v["median_cents"] for k, v in table["steps"].items()},
        "pitch": pitch,
        "bit5_comparisons": rows,
        "bit5_inert": inert,
        "limits": registration["limits"],
    }
    write_bytes(decision_path, json_bytes(result))
    print(
        json.dumps(
            {
                "native": True,
                "reception": result["reception"],
                "pitch_classification": pitch["classification"],
                "cents": None
                if table is None
                else {k: round(v["median_cents"], 1) for k, v in table["steps"].items()},
                "bit5_inert": inert,
                "bit5": [
                    {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}
                    for r in rows
                ],
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
