"""Check the polyphony test: exact reception, then how many voices each stack played."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.globals import pattern_chain
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.polyphony_method import SETTINGS, presence, voice_levels
from scripts.prepare_polyphony_test import (
    CHAIN,
    CYCLES,
    DIRECTORY,
    LIMITS,
    REGISTRATION,
    SOLO_STEPS,
    SOUND_ORDER,
    STACKS,
    VOICES,
)

DECISION = "polyphony-decision-001.json"
CYCLE_STEPS = 32


def evaluate(cycles):
    """Majority presence per stack, counts, and which voice-limit model fits."""
    stacks = {}
    for step, sounds in STACKS.items():
        rows = [c[16 + step] for c in cycles if c.get(16 + step) is not None]
        if not rows:
            stacks[step] = None
            continue
        votes = np.array([r["present"] for r in rows])
        majority = votes.sum(axis=0) * 2 > len(rows)
        requested = [SOUND_ORDER.index(s) for s in sounds]
        present = [SOUND_ORDER[v] for v in requested if majority[v]]
        stacks[step] = {
            "requested": sounds,
            "present": present,
            "count": len(present),
            "unexpected": [
                SOUND_ORDER[v]
                for v in range(len(SOUND_ORDER))
                if majority[v] and v not in requested
            ],
            "median_db_vs_solo": np.median([r["db_vs_solo"] for r in rows], axis=0).tolist(),
        }
    support = {
        f"voice_limit_{L}": all(
            v is not None and v["count"] == min(len(v["requested"]), L) for v in stacks.values()
        )
        for L in LIMITS
    }
    supported = [name for name, ok in support.items() if ok]
    return {
        "stacks": {str(k): v for k, v in stacks.items()},
        "model_support": support,
        "classification": supported[0] if len(supported) == 1 else "other_or_inconclusive",
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / "scripts/polyphony_method.py") != registration["method_script_sha256"]
        or registration["method_settings"] != SETTINGS
        or registration["stacks"] != {str(k): v for k, v in STACKS.items()}
    ):
        raise ValueError("Frozen method or plan changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "polyphony-measurements-001.json"
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
        "planned_chain": pattern_chain(actual) == CHAIN,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    }
    native = {
        "analysis_version": "polyphony-native-check-0.1",
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
    frequencies = [VOICES[s] for s in SOUND_ORDER]
    first, levels = voice_levels(playback, CYCLE_STEPS * CYCLES, frequencies, SETTINGS)
    solo = {SOUND_ORDER.index(s): step for s, step in SOLO_STEPS.items()}
    cycles = presence(levels, solo, [16 + s for s in STACKS], CYCLE_STEPS, SETTINGS)
    cycles = [{k: v for k, v in c.items()} for c in cycles]
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "polyphony-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "sound_order": SOUND_ORDER,
                "step_levels": [None if np.isnan(row).any() else row.tolist() for row in levels],
                "cycles": [{str(k): v for k, v in c.items()} for c in cycles],
            }
        ),
    )
    result = evaluate(cycles)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "polyphony-decision-0.1",
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
                "counts": {
                    k: None if v is None else [len(v["requested"]), v["count"], v["unexpected"]]
                    for k, v in result["stacks"].items()
                },
            }
        )
    )


if __name__ == "__main__":
    main()
