"""Check the pitch-code law test: exact reception, then per-step pitches."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.notes import step_parameters
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import _replace_pattern_data, melodic_notes, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_key_scale_grid_method import SETTINGS, decide, intervals, step_frequencies
from scripts.prepare_pitch_law_test import DIRECTORY, MODELS, PITCH_CODES, REGISTRATION

DECISION = "pitch-law-decision-001.json"


def writer_checks(base, actual):
    source, data = pattern_data(base, 1), pattern_data(actual, 1)
    cells = {48 * (s - 1) + 6 + i for s in range(1, 17) for i in range(3)}
    cells |= {768 + 16 * (s - 1) + 2 for s in range(1, 17)}
    parameters = step_parameters(actual, 1, 3)
    return {
        "native_valid": encode_packets(actual.packets) == actual.encoded_body,
        "only_Pattern1_changed": _replace_pattern_data(actual, 1, source) == base.packets,
        "only_Sound3_cells_changed": all(
            data[i] == source[i] for i in range(1032) if i not in cells
        ),
        "all_keys_1": melodic_notes(actual, 1, 3) == [1] * 16,
        "pitch_codes_as_planned": [p["pitch"] for p in parameters] == PITCH_CODES,
    }


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
    source_path = root / registration["source_artifact"]
    native_path = folder / "hardware-recapture-results-001.json"
    pitch_path = folder / "key-frequency-results-001.json"
    decision_path = root / "experiments" / DECISION
    validate_outputs(
        [native_path, pitch_path, decision_path],
        [capture, playback, artifact_path, target_path, source_path],
        False,
    )
    if sha256_file(target_path) != registration["edited_artifact_sha256"]:
        raise ValueError("Registered target changed")
    artifact = load_artifact(artifact_path)
    capture_hash = sha256_file(capture)
    if artifact.metadata["source_sha256"] != capture_hash:
        raise ValueError("Analysis artifact is not from capture.wav")
    base = decode_artifact(load_artifact(source_path))
    target = decode_artifact(load_artifact(target_path))
    actual = decode_artifact(artifact)
    checks = dict(
        writer_checks(base, actual),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        entire_actual_body_and_packets_match_target=actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        capture_is_new=capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
    )
    native = {
        "analysis_version": "pitch-law-native-check-0.1",
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
        raise ValueError("Native reception failed; report retained")
    info, steps = step_frequencies(playback, SETTINGS)
    table = intervals(steps)
    write_bytes(
        pitch_path,
        json_bytes(
            {
                "analysis_version": "pitch-law-frequencies-0.1",
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
    decision = decide(table, MODELS)
    cents = (
        None if table is None else {str(k): v["median_cents"] for k, v in table["steps"].items()}
    )
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "pitch-law-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "frequency_results_sha256": sha256_file(pitch_path),
                "measured_cents": cents,
                **decision,
                "limits": registration["limits"],
            }
        ),
    )
    print(
        json.dumps(
            {
                "native": native["passed"],
                "cents": None
                if cents is None
                else {k: None if v is None else round(v, 1) for k, v in cents.items()},
                "expected": dict(zip(map(str, range(1, 17)), MODELS["semitone_per_code"])),
                "classification": decision["classification"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
