"""Check the long melodic import: exact reception, then the long note's length and pitches."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, sound_data
from po33_re.formats.patterns import melodic_notes
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_memory_test import total_capacity
from scripts.long_note_method import SETTINGS, decide, measure
from scripts.prepare_long_melodic_test import (
    CAPACITY,
    DIRECTORY,
    EXPECTED_HZ,
    EXPECTED_MS,
    NATIVE_CODES,
    NOTES,
    REGISTRATION,
    TOTAL,
)

DECISION = "long-melodic-decision-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if sha256_file(root / "scripts/long_note_method.py") != registration["method_script_sha256"]:
        raise ValueError("Frozen method changed since registration")
    if (
        registration["method_settings"] != SETTINGS
        or registration["expected_duration_ms"] != EXPECTED_MS
        or registration["expected_quarter_hz"] != EXPECTED_HZ
    ):
        raise ValueError("Frozen settings or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "long-note-measurements-001.json"
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
    record = sound_data(actual, 5)
    checks = {
        "native_valid": encode_packets(actual.packets) == actual.encoded_body,
        "sound6_record_matches_target": record == sound_data(target, 5),
        "sound6_capacity_and_end": len(record) == 9 + CAPACITY
        and int.from_bytes(record[4:8], "little") == NATIVE_CODES,
        "total_capacity": total_capacity(actual) == TOTAL,
        "planned_notes": melodic_notes(actual, 1, 6) == NOTES,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "long-melodic-native-check-0.1",
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
    info, loops = measure(playback, SETTINGS)
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "long-melodic-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                **info,
                "loops": loops,
            }
        ),
    )
    decision = decide(loops, EXPECTED_MS, EXPECTED_HZ, SETTINGS)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "long-melodic-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "measurements_sha256": sha256_file(measure_path),
                "expected_duration_ms": EXPECTED_MS,
                **decision,
                "classification": "whole_sample_plays_in_order"
                if decision["duration_holds"] and decision["pitch_holds"]
                else "other_or_inconclusive",
                "limits": registration["limits"],
            }
        ),
    )
    print(
        json.dumps(
            {
                "native": True,
                "median_duration_ms": decision["median_duration_ms"],
                "expected_ms": round(EXPECTED_MS, 1),
                "duration_holds": decision["duration_holds"],
                "quarter_cents_off": [q["median_cents_off"] for q in decision["quarters"]],
                "pitch_holds": decision["pitch_holds"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
