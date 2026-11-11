"""Check the bit-5 glide test: exact reception, then early/late pitch, level and duration."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.notes import step_parameters, unknown_bits
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.drum_slice_duration_method import SETTINGS as DURATION_SETTINGS
from scripts.drum_slice_duration_method import step_durations
from scripts.pattern1_key_scale_grid_method import step_frequencies
from scripts.polyphony_method_exploratory import SETTINGS as LEVEL_SETTINGS
from scripts.polyphony_method_exploratory import voice_levels
from scripts.prepare_bit5_glide_test import (
    BASE_HZ,
    BITS,
    DIRECTORY,
    EARLY,
    EXPECTED_HZ,
    LATE,
    PATTERN,
    PITCHES,
    REGISTRATION,
    TOLERANCES,
)

DECISION = "bit5-glide-decision-001.json"


def cents_from_target(steps, step):
    values = [f for f in steps.get(step, []) if f is not None]
    if not values:
        return None
    return float(1200 * np.log2(np.median(values) / EXPECTED_HZ[step]))


def evaluate(early, late, levels_db, durations):
    rows = {}
    for step in range(1, 17):
        rows[step] = {
            "pitch": PITCHES[step - 1],
            "bit5": BITS[step - 1],
            "early_cents_from_target": cents_from_target(early, step),
            "late_cents_from_target": cents_from_target(late, step),
            "level_db": levels_db[step],
            "duration_ms": float(np.median(durations[step])) if PITCHES[step - 1] == 25 else None,
        }
    plain = [s for s in range(1, 17) if not BITS[s - 1]]
    flagged = [s for s in range(1, 17) if BITS[s - 1]]

    def group(steps, pitch, key):
        values = [
            rows[s][key] for s in steps if rows[s]["pitch"] == pitch and rows[s][key] is not None
        ]
        return float(np.median(values)) if values else None

    summary = {}
    for pitch in (7, 25):
        summary[pitch] = {
            key: {"plain": group(plain, pitch, key), "flagged": group(flagged, pitch, key)}
            for key in (
                "early_cents_from_target",
                "late_cents_from_target",
                "level_db",
                "duration_ms",
            )
        }

    def diff(pitch, key):
        a, b = summary[pitch][key]["flagged"], summary[pitch][key]["plain"]
        return None if a is None or b is None else a - b

    inert = (
        all(
            abs(diff(p, "early_cents_from_target")) <= TOLERANCES["cents"]
            and abs(diff(p, "late_cents_from_target")) <= TOLERANCES["cents"]
            and abs(diff(p, "level_db")) <= TOLERANCES["db"]
            for p in (7, 25)
        )
        and abs(diff(25, "duration_ms")) <= TOLERANCES["ms"]
    )
    no_glide = (
        all(
            abs(summary[p]["early_cents_from_target"]["flagged"]) <= TOLERANCES["cents"]
            and abs(summary[p]["early_cents_from_target"]["plain"]) >= TOLERANCES["glide_cents"]
            for p in (7, 25)
        )
        and diff(25, "duration_ms") < -TOLERANCES["ms"]
    )
    support = {"bit5_inert": inert, "bit5_no_glide": no_glide}
    holding = [m for m, ok in support.items() if ok]
    return {
        "steps": {str(k): v for k, v in rows.items()},
        "summary": {str(k): v for k, v in summary.items()},
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
        "scripts/polyphony_method_exploratory.py": registration["level_method_script_sha256"],
    }
    if any(sha256_file(root / path) != pin for path, pin in pins.items()):
        raise ValueError("A frozen method changed since registration")
    if registration["early_settings"] != EARLY or registration["late_settings"] != LATE:
        raise ValueError("Frozen settings changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "bit5-glide-measurements-001.json"
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
        "planned_notes": [p["pitch"] for p in step_parameters(actual, PATTERN, 1)] == PITCHES
        and unknown_bits(actual, PATTERN, 1) == BITS,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "bit5-glide-native-check-0.1",
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
    info, early = step_frequencies(playback, EARLY)
    _, late = step_frequencies(playback, LATE)
    frequencies = sorted(set(EXPECTED_HZ.values()))
    _, levels = voice_levels(playback, 16 * EARLY["loops"], frequencies, LEVEL_SETTINGS)
    levels_db = {}
    for step, hz in EXPECTED_HZ.items():
        column = frequencies.index(hz)
        values = [levels[c * 16 + step - 1, column] for c in range(EARLY["loops"])]
        levels_db[step] = float(20 * np.log10(np.median(values)))
    _, durations = step_durations(playback, DURATION_SETTINGS)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "bit5-glide-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                **info,
                "base_hz": BASE_HZ,
                "early_hz": {str(k): v for k, v in early.items()},
                "late_hz": {str(k): v for k, v in late.items()},
                "levels_db": {str(k): v for k, v in levels_db.items()},
                "step_durations_ms": {str(k): v for k, v in durations.items()},
            }
        ),
    )
    result = evaluate(early, late, levels_db, durations)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "bit5-glide-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "measurements_sha256": sha256_file(measure_path),
                **result,
                "limits": registration["limits"],
            }
        ),
    )
    print(
        json.dumps(
            {
                "native": True,
                "classification": result["classification"],
                "model_support": result["model_support"],
                "summary": {
                    p: {
                        k: {g: None if x is None else round(x, 1) for g, x in v.items()}
                        for k, v in s.items()
                    }
                    for p, s in result["summary"].items()
                },
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
