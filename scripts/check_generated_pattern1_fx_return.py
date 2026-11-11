"""Require every byte of both generated effect targets, gating clear on accepted down data."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.prepare_generated_pattern1_fx_return import LEGS, REGISTRATION, return_checks


def reception_checks(base, target, actual, leg, baseline):
    checks = dict(
        return_checks(base, actual, leg),
        entire_actual_body_and_packets_match_target=actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
    )
    if leg == "clear":
        checks["entire_independent_clear_body_and_packets_return"] = (
            actual.packets == baseline.packets and actual.encoded_body == baseline.encoded_body
        )
    return checks


def require_down_result(result, registration_hash, capture_hash, artifact_hash):
    if (
        not result["passed"]
        or not all(result["checks"].values())
        or result["registration_sha256"] != registration_hash
        or result["capture_sha256"] != capture_hash
        or result["artifact_sha256"] != artifact_hash
    ):
        raise ValueError("Exact independent down reception must pass before clear")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leg", required=True, choices=list(LEGS))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    spec = next(
        item for item in registration["expected_capture_sequence"] if item["leg"] == args.leg
    )
    folder = root / "experiments" / spec["experiment_id"]
    down_folder = root / "experiments" / LEGS["down"]["experiment_id"]
    source_path = (
        root / registration["source_artifact"]
        if args.leg == "down"
        else down_folder / "edited.symbols.npz"
    )
    target_path = folder / "edited.symbols.npz"
    capture_path = folder / "capture.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    output = folder / "hardware-recapture-results-001.json"
    baseline_path = root / registration["independent_clear_artifact"]
    validate_outputs(
        [output],
        [registration_path, source_path, target_path, capture_path, artifact_path, baseline_path],
        False,
    )
    pins = [
        (root / registration["source_artifact"], registration["source_artifact_sha256"]),
        (root / registration["source_capture"], registration["source_capture_sha256"]),
        (root / registration["source_observation"], registration["source_observation_sha256"]),
        (baseline_path, registration["independent_clear_artifact_sha256"]),
        (
            root / registration["independent_clear_capture"],
            registration["independent_clear_capture_sha256"],
        ),
        (
            root / registration["independent_clear_observation"],
            registration["independent_clear_observation_sha256"],
        ),
    ]
    for leg in registration["expected_capture_sequence"]:
        directory = root / "experiments" / leg["experiment_id"]
        pins.extend(
            [
                (directory / "edited.symbols.npz", leg["edited_artifact_sha256"]),
                (directory / "restore.wav", leg["restore_wav_sha256"]),
                (directory / "software-validation.json", leg["software_validation_sha256"]),
            ]
        )
    if any(sha256_file(path) != digest for path, digest in pins):
        raise ValueError("Frozen generated source/targets or clear baseline identity differs")
    recorded = load_artifact(artifact_path)
    capture_hash = sha256_file(capture_path)
    forbidden = {
        registration["source_capture_sha256"],
        registration["independent_clear_capture_sha256"],
        *(item["restore_wav_sha256"] for item in registration["expected_capture_sequence"]),
    }
    predecessor_path = None
    if args.leg == "clear":
        predecessor_path = down_folder / "hardware-recapture-results-001.json"
        down_capture_hash = sha256_file(down_folder / "capture.wav")
        require_down_result(
            json.loads(predecessor_path.read_text()),
            sha256_file(registration_path),
            down_capture_hash,
            sha256_file(down_folder / "derived/analysis-001/capture.symbols.npz"),
        )
        forbidden.add(down_capture_hash)
    if recorded.metadata["source_sha256"] != capture_hash or capture_hash in forbidden:
        raise ValueError("Independent new physical capture identity differs")
    base, target, actual, baseline = [
        decode_artifact(item)
        for item in (
            load_artifact(source_path),
            load_artifact(target_path),
            recorded,
            load_artifact(baseline_path),
        )
    ]
    checks = reception_checks(base, target, actual, args.leg, baseline)
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "fixed-footer-return-global7-native-recapture-check-0.1",
                "hardware_verified": False,
                "passed": all(checks.values()),
                "checks": checks,
                "leg": args.leg,
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": capture_hash,
                "artifact_sha256": sha256_file(artifact_path),
                "artifact_path": artifact_path.relative_to(root).as_posix(),
                "native_frame": frame_report(actual),
                "audible_effect_evaluated": False,
                "predecessor_native_results_sha256": sha256_file(predecessor_path)
                if predecessor_path
                else None,
                "FX_writer_enabled": False,
                "limits": registration["limits"],
            }
        ),
    )
    if not all(checks.values()):
        raise ValueError("Fixed-return reception differs; failed report retained")


if __name__ == "__main__":
    main()
