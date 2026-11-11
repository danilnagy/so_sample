"""Check the FX direction test: reception, plain notes forward, and a direction per effect."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.fx_descriptor_method import _prepare
from scripts.fx_direction_method import SETTINGS, describe_notes
from scripts.prepare_fx_direction_test import (
    CHAIN,
    CONTROL_PATTERN,
    DIRECTORY,
    HELD,
    MODELS,
    NOTE_STEPS,
    REGISTRATION,
    TEMPO,
)

DECISION = "fx-direction-decision-001.json"
STEP_SECONDS = 60 / TEMPO / 4


def sequence(note):
    return [None if w is None else w["segment"] for w in note["windows"]]


def matches(seq, model):
    return all(m == "any" or s == m for s, m in zip(seq, model, strict=True))


def classify(notes):
    fits = [
        name for name, model in MODELS.items() if all(matches(sequence(n), model) for n in notes)
    ]
    return fits[0] if len(fits) == 1 else "described"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    pins = {
        "scripts/fx_direction_method.py": registration["method_script_sha256"],
        "scripts/fx_descriptor_method.py": registration["descriptor_method_script_sha256"],
    }
    if any(sha256_file(root / path) != pin for path, pin in pins.items()):
        raise ValueError("A frozen method changed since registration")
    if registration["method_settings"] != SETTINGS or registration["models"] != MODELS:
        raise ValueError("Frozen settings or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "fx-direction-measurements-001.json"
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
        "analysis_version": "fx-direction-native-check-0.1",
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
    note_times, labels = [], []
    for i, pattern in enumerate(CHAIN):
        for step in NOTE_STEPS:
            note_times.append(first + (i * 16 + step - 1) * STEP_SECONDS)
            labels.append((pattern, step))
    reference = labels.index((CONTROL_PATTERN, 1))
    notes = describe_notes(playback, note_times, reference, SETTINGS)
    by_pattern = {
        p: [n for (pp, _), n in zip(labels, notes, strict=True) if pp == p] for p in CHAIN
    }
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "fx-direction-measurements-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "notes": [
                    {"pattern": p, "step": s, **n} for (p, s), n in zip(labels, notes, strict=True)
                ],
            }
        ),
    )
    plain = [by_pattern[CONTROL_PATTERN][k] for k in range(4)] + [
        by_pattern[p][0] for p in CHAIN if p != CONTROL_PATTERN
    ]
    effects = {}
    for pattern, fx in HELD.items():
        held = by_pattern[pattern][1:]
        effects[str(fx)] = {
            "pattern": pattern,
            "sequences": [sequence(n) for n in held],
            "onsets": [n["onsets"] for n in held],
            "levels_db": [
                [None if w is None else round(w["level_db"]) for w in n["windows"]] for n in held
            ],
            "classification": classify(held),
        }
    decision = {
        "analysis_version": "fx-direction-decision-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": sha256_file(native_path),
        "measurements_sha256": sha256_file(measure_path),
        "hypotheses": {
            "exact_reception": checks["entire_actual_body_and_packets_match_target"],
            "plain_notes_forward": all(matches(sequence(n), MODELS["forward"]) for n in plain),
        },
        "effects": effects,
        "limits": registration["limits"],
    }
    write_bytes(decision_path, json_bytes(decision))
    print(json.dumps({"hypotheses": decision["hypotheses"]}))
    for fx, v in effects.items():
        print(f"FX {fx:>2}: {v['classification']:>10} {v['sequences']} onsets {v['onsets']}")


if __name__ == "__main__":
    main()
