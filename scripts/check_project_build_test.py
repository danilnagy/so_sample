"""Check the project build test: exact reception, then tempo, swing and the melody."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.polyphony_method_exploratory import voice_levels
from scripts.prepare_project_build_test import (
    DIRECTORY,
    EXPECTED,
    LEVEL_SETTINGS,
    MELODY_KEY1_HZ,
    ONSET_HAT,
    ONSET_KICK,
    REGISTRATION,
    TOLERANCES,
)
from scripts.swing_onset_method import onsets

DECISION = "project-build-decision-001.json"


def hat_offsets(kicks, hats):
    """Each hat onset minus the latest kick onset before it."""
    kicks = np.asarray(kicks)
    offsets = []
    for hat in hats:
        earlier = kicks[kicks < hat]
        if len(earlier):
            offsets.append(float(hat - earlier.max()))
    return offsets


def evaluate(kicks, hats, melody_db):
    intervals = np.diff(kicks).tolist()
    offsets = hat_offsets(kicks, hats)
    kick_interval = float(np.median(intervals)) if intervals else None
    hat_offset = float(np.median(offsets)) if offsets else None
    hypotheses = {
        "tempo_100": kick_interval is not None
        and abs(kick_interval - EXPECTED["kick_interval_s"]) <= TOLERANCES["seconds"],
        "swing_4": hat_offset is not None
        and abs(hat_offset - EXPECTED["hat_offset_s"]) <= TOLERANCES["seconds"],
        "melody_first_note": melody_db["step1"] - melody_db["step2"] >= TOLERANCES["melody_db"],
    }
    return {
        "kick_interval_s": kick_interval,
        "hat_offset_s": hat_offset,
        "melody_db": melody_db,
        "hypotheses": hypotheses,
        "classification": "project_plays_as_built" if all(hypotheses.values()) else "other",
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    pins = {
        "scripts/swing_onset_method.py": registration["onset_method_script_sha256"],
        "scripts/polyphony_method_exploratory.py": registration["level_method_script_sha256"],
    }
    if any(sha256_file(root / path) != pin for path, pin in pins.items()):
        raise ValueError("A frozen method changed since registration")
    if (
        registration["onset_settings"] != {"kick": ONSET_KICK, "hat": ONSET_HAT}
        or registration["level_settings"] != LEVEL_SETTINGS
        or registration["expected"] != EXPECTED
    ):
        raise ValueError("Frozen settings changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "project-build-measurements-001.json"
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
        "analysis_version": "project-build-native-check-0.1",
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
    kicks = onsets(playback, ONSET_KICK)
    hats = onsets(playback, ONSET_HAT)
    _, levels = voice_levels(playback, 2, [MELODY_KEY1_HZ], LEVEL_SETTINGS)
    melody_db = {
        "step1": float(20 * np.log10(levels[0, 0])),
        "step2": float(20 * np.log10(levels[1, 0])),
    }
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "project-build-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "kick_onsets_s": kicks,
                "hat_onsets_s": hats,
                "melody_db": melody_db,
            }
        ),
    )
    result = evaluate(kicks, hats, melody_db)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "project-build-decision-0.1",
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
                "kick_interval_s": None
                if result["kick_interval_s"] is None
                else round(result["kick_interval_s"], 4),
                "hat_offset_s": None
                if result["hat_offset_s"] is None
                else round(result["hat_offset_s"], 4),
                "melody_db": {k: round(v, 1) for k, v in melody_db.items()},
                "hypotheses": result["hypotheses"],
                "classification": result["classification"],
            }
        )
    )


if __name__ == "__main__":
    main()
