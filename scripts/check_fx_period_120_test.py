"""Check the tempo-sync test: exact reception, then whether the loop periods halved at 120 BPM."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.fx_descriptor_method import _prepare
from scripts.fx_period_median_method import SETTINGS, period_ms, pitch_track
from scripts.prepare_fx_period_120_test import (
    CHAIN,
    CONTROL_PATTERN,
    DIRECTORY,
    HELD,
    MODELS,
    REGISTRATION,
    TEMPO,
    model_support,
)

DECISION = "fx-period-120-decision-001.json"
STEP_SECONDS = 60 / TEMPO / 4
HELD_NOTE_STEP = 5


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    pins = {
        "scripts/fx_period_median_method.py": registration["method_script_sha256"],
        "scripts/fx_period_method.py": registration["base_method_script_sha256"],
        "scripts/fx_descriptor_method.py": registration["descriptor_method_script_sha256"],
    }
    if any(sha256_file(root / path) != pin for path, pin in pins.items()):
        raise ValueError("A frozen method changed since registration")
    models = {m: {str(k): v for k, v in p.items()} for m, p in MODELS.items()}
    if registration["method_settings"] != SETTINGS or registration["models_ms"] != models:
        raise ValueError("Frozen settings or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "fx-period-120-measurements-001.json"
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
        "analysis_version": "fx-period-120-native-check-0.1",
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
    note_times = [first + (i * 16 + HELD_NOTE_STEP - 1) * STEP_SECONDS for i in range(len(CHAIN))]
    tracks = pitch_track(playback, note_times, SETTINGS)
    periods = {
        pattern: period_ms(track, SETTINGS) for pattern, track in zip(CHAIN, tracks, strict=True)
    }
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "fx-period-120-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "tracks_cents": {str(p): t for p, t in zip(CHAIN, tracks, strict=True)},
                "periods": {
                    str(p): {"period_ms": v[0], "mismatch": v[1]} for p, v in periods.items()
                },
            }
        ),
    )
    effects = {
        str(fx): {
            "pattern": pattern,
            "period_ms": periods[pattern][0],
            "mismatch": periods[pattern][1],
        }
        for pattern, fx in HELD.items()
    }
    support = model_support({fx: periods[pattern][0] for pattern, fx in HELD.items()})
    holding = [m for m, ok in support.items() if ok]
    decision = {
        "analysis_version": "fx-period-120-decision-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": sha256_file(native_path),
        "measurements_sha256": sha256_file(measure_path),
        "hypotheses": {
            "exact_reception": checks["entire_actual_body_and_packets_match_target"],
            "control_has_no_period": periods[CONTROL_PATTERN][0] is None,
        },
        "effects": effects,
        "model_support": support,
        "classification": holding[0] if len(holding) == 1 else "other_or_inconclusive",
        "control": {
            "period_ms": periods[CONTROL_PATTERN][0],
            "mismatch": periods[CONTROL_PATTERN][1],
        },
        "limits": registration["limits"],
    }
    write_bytes(decision_path, json_bytes(decision))
    print(
        json.dumps(
            {
                "hypotheses": decision["hypotheses"],
                "classification": decision["classification"],
                "control": decision["control"],
            }
        )
    )
    for fx, v in effects.items():
        median = None if v["mismatch"] is None else round(v["mismatch"], 1)
        print(f"FX {fx:>2}: period {v['period_ms']} ms, mismatch {median} cents")


if __name__ == "__main__":
    main()
