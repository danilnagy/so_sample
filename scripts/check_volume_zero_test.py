"""Check the volume-code-0 test: exact reception, then the registered level decision."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.notes import step_parameters
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_volume_gain_method import SETTINGS, levels_db, step_levels
from scripts.prepare_volume_zero_test import DIRECTORY, REGISTRATION, VOLUME_CODES, decide_zero

DECISION = "volume-zero-decision-001.json"


def writer_checks(base, actual):
    source, data = pattern_data(base, 1), pattern_data(actual, 1)
    primary = {48 * (s - 1) + 6 + i for s in range(1, 17) for i in range(3)}
    parameters = step_parameters(actual, 1, 3)
    return {
        "native_valid": encode_packets(actual.packets) == actual.encoded_body,
        "only_Pattern1_changed": _replace_pattern_data(actual, 1, source) == base.packets,
        "only_Sound3_primary_bytes_changed": all(
            data[i] == source[i] for i in range(1032) if i not in primary
        ),
        "volume_codes_as_planned": [p["volume"] for p in parameters] == VOLUME_CODES,
        "pitch_codes_unchanged_at_13": all(p["pitch"] == 13 for p in parameters),
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / "scripts/pattern1_volume_gain_method.py")
        != registration["method_script_sha256"]
    ):
        raise ValueError("Frozen method changed since registration")
    if registration["method_settings"] != SETTINGS or registration["volume_codes"] != VOLUME_CODES:
        raise ValueError("Frozen settings or codes changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    source_path = root / registration["source_artifact"]
    native_path = folder / "hardware-recapture-results-001.json"
    level_path = folder / "level-results-001.json"
    decision_path = root / "experiments" / DECISION
    validate_outputs(
        [native_path, level_path, decision_path],
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
        "analysis_version": "volume-zero-native-check-0.1",
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
    info, steps = step_levels(playback, SETTINGS)
    table = levels_db(steps)
    write_bytes(
        level_path,
        json_bytes(
            {
                "analysis_version": "volume-zero-levels-0.1",
                "hardware_verified": False,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                **info,
                "step_rms": {str(k): v for k, v in steps.items()},
                "levels": None
                if table is None
                else {
                    "step1_rms": table["step1_rms"],
                    "steps": {str(k): v for k, v in table["steps"].items()},
                },
            }
        ),
    )
    by_step = None if table is None else {s: v["median_db"] for s, v in table["steps"].items()}
    decision = (
        {"classification": "other_or_inconclusive", "reason": "no reference level"}
        if by_step is None
        else decide_zero(by_step, registration["predicted_nonzero_db_vs_step1"])
    )
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "volume-zero-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "native_results_sha256": sha256_file(native_path),
                "level_results_sha256": sha256_file(level_path),
                "measured_db_by_step": None
                if by_step is None
                else {str(k): v for k, v in by_step.items()},
                "predicted_nonzero_db_vs_step1": registration["predicted_nonzero_db_vs_step1"],
                **decision,
                "limits": registration["limits"],
            }
        ),
    )
    print(
        json.dumps(
            {
                "native": native["passed"],
                "db_by_step": None
                if by_step is None
                else {f"{k} (code {VOLUME_CODES[k - 1]})": round(v, 2) for k, v in by_step.items()},
                **decision,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
