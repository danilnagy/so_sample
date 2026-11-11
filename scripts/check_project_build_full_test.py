"""Check the full project build: exact reception, tempo, chain cycle and the melody."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.polyphony_method_exploratory import voice_levels
from scripts.prepare_project_build_full_test import (
    DIRECTORY,
    EXPECTED,
    LEVEL_SETTINGS,
    MELODY_KEY1_HZ,
    ONSET_KICK,
    ONSET_SNARE,
    REGISTRATION,
    TOLERANCES,
)
from scripts.swing_onset_method import onsets

DECISION = "project-build-full-decision-001.json"
SNARE_PAIR_S = 8 * EXPECTED["kick_interval_s"] / 4  # steps 5 and 13 are 8 steps apart


def snare_cycle_intervals(snares):
    """Intervals between successive snare bursts, skipping the pair inside one pattern."""
    times = np.asarray(snares)
    bursts = []
    for t in times:
        if not bursts or t - bursts[-1][-1] > 2 * SNARE_PAIR_S:
            bursts.append([t])
        else:
            bursts[-1].append(t)
    starts = [b[0] for b in bursts]
    return np.diff(starts).tolist()


def evaluate(kicks, snares, melody_db):
    kick_intervals = np.diff(kicks).tolist()
    cycles = snare_cycle_intervals(snares)
    kick = float(np.median(kick_intervals)) if kick_intervals else None
    cycle = float(np.median(cycles)) if cycles else None
    hypotheses = {
        "tempo_128": kick is not None
        and abs(kick - EXPECTED["kick_interval_s"]) <= TOLERANCES["kick_s"],
        "chain_8": cycle is not None
        and abs(cycle - EXPECTED["chain_cycle_s"]) <= TOLERANCES["cycle_s"],
        "melody_first_note": melody_db["step1"] - melody_db["step2"] >= TOLERANCES["melody_db"],
    }
    return {
        "kick_interval_s": kick,
        "chain_cycle_s": cycle,
        "snare_burst_intervals_s": cycles,
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
        registration["onset_settings"] != {"kick": ONSET_KICK, "snare": ONSET_SNARE}
        or registration["level_settings"] != LEVEL_SETTINGS
        or registration["expected"] != EXPECTED
    ):
        raise ValueError("Frozen settings changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "project-build-full-measurements-001.json"
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
        "analysis_version": "project-build-full-native-check-0.1",
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
    snares = onsets(playback, ONSET_SNARE)
    _, levels = voice_levels(playback, 2, [MELODY_KEY1_HZ], LEVEL_SETTINGS)
    melody_db = {
        "step1": float(20 * np.log10(levels[0, 0])),
        "step2": float(20 * np.log10(levels[1, 0])),
    }
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "project-build-full-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "kick_onsets_s": kicks,
                "snare_onsets_s": snares,
                "melody_db": melody_db,
            }
        ),
    )
    result = evaluate(kicks, snares, melody_db)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "project-build-full-decision-0.1",
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
                "chain_cycle_s": None
                if result["chain_cycle_s"] is None
                else round(result["chain_cycle_s"], 3),
                "melody_db": {k: round(v, 1) for k, v in melody_db.items()},
                "hypotheses": result["hypotheses"],
                "classification": result["classification"],
            }
        )
    )


if __name__ == "__main__":
    main()
