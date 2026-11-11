"""Check the third sample-memory step: exact reception of 917504 codes, then Sound9."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.drum_import import drum_ids
from po33_re.formats.packets import (
    decode_artifact,
    encode_packets,
    frame_report,
    sound_data,
)
from po33_re.formats.patterns import drum_notes
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_memory_test import total_capacity
from scripts.pattern1_key_scale_grid_method import decide, intervals, step_frequencies
from scripts.prepare_sample_memory_step3 import (
    CAPACITY,
    DIRECTORY,
    KEYS,
    MODELS,
    REGISTRATION,
    SETTINGS,
    SLOT,
    TOTAL,
    absolute_decision,
)

DECISION = "sample-memory-decision-003.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / "scripts/pattern1_key_scale_grid_method.py")
        != registration["method_script_sha256"]
    ):
        raise ValueError("Frozen method changed since registration")
    if registration["method_settings"] != SETTINGS or registration["models_cents"] != MODELS:
        raise ValueError("Frozen settings or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    pitch_path = folder / "key-frequency-results-001.json"
    decision_path = root / "experiments" / DECISION
    validate_outputs(
        [native_path, pitch_path, decision_path],
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
        "sound9_kit_matches_target": all(
            sound_data(actual, sid) == sound_data(target, sid) for sid in drum_ids(SLOT)
        )
        and len(sound_data(actual, drum_ids(SLOT)[0])) == 9 + CAPACITY,
        "sound1_buffer_and_sound10_references_kept": sound_data(actual, 0) == sound_data(target, 0)
        and all(sound_data(actual, sid) == sound_data(target, sid) for sid in drum_ids(10)),
        "total_capacity": total_capacity(actual) == TOTAL,
        "planned_notes": drum_notes(actual, 1, SLOT) == KEYS
        and drum_notes(actual, 1, 11) == [None] * 16,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "sample-memory-native-check-0.3",
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
    write_bytes(
        pitch_path,
        json_bytes(
            {
                "analysis_version": "sample-memory-frequencies-0.3",
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
            }
        ),
    )
    decision = decide(table, MODELS, SETTINGS)
    absolute = absolute_decision(None if table is None else table["step1_hz"])
    cents = (
        None if table is None else {str(k): v["median_cents"] for k, v in table["steps"].items()}
    )
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "sample-memory-decision-0.3",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "frequency_results_sha256": sha256_file(pitch_path),
                "step1_hz": None if table is None else table["step1_hz"],
                "measured_cents": cents,
                **decision,
                "absolute": absolute,
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
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
