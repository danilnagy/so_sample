"""Check both exact first-pair targets, then compare frozen first-tone order alternatives."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_fx_nibble_audio import PARAMETERS, audio_report, compare_audio
from scripts.prepare_generated_pattern1_fx_nibble_pair import LEGS, REGISTRATION, probe_checks


def reception_checks(base, target, actual, spec):
    return dict(
        probe_checks(base, actual, spec["leg"]),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == spec["expected_body_sha256"],
        entire_actual_body_and_packets_match_target=actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
    )


def require_native_result(result, registration_hash, capture_hash, artifact_hash):
    if (
        not result["passed"]
        or not all(result["checks"].values())
        or result["registration_sha256"] != registration_hash
        or result["capture_sha256"] != capture_hash
        or result["artifact_sha256"] != artifact_hash
    ):
        raise ValueError("Both exact independent native targets must pass before audio")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leg", choices=list(LEGS))
    parser.add_argument("--audio", action="store_true")
    args = parser.parse_args()
    if bool(args.leg) == args.audio:
        parser.error("Choose one --leg a/b for native reception, or --audio for the gated pair")
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["source_artifact"]
    specs = registration["expected_capture_sequence"]
    pins = [
        (source_path, registration["source_artifact_sha256"]),
        (root / registration["source_capture"], registration["source_capture_sha256"]),
        (root / registration["source_observation"], registration["source_observation_sha256"]),
        (root / "scripts/pattern1_fx_nibble_audio.py", registration["audio_method_script_sha256"]),
        (
            root / "scripts/sound3_pitch_frequency_analysis.py",
            registration["frequency_fit_helper_sha256"],
        ),
    ]
    for spec in specs:
        folder = root / "experiments" / spec["experiment_id"]
        pins.extend(
            [
                (folder / "edited.symbols.npz", spec["edited_artifact_sha256"]),
                (folder / "restore.wav", spec["restore_wav_sha256"]),
                (folder / "software-validation.json", spec["software_validation_sha256"]),
            ]
        )
    if (
        any(sha256_file(path) != digest for path, digest in pins)
        or registration["audio_parameters"] != PARAMETERS
    ):
        raise ValueError("Frozen source/targets or first-tone method identity differs")
    registration_hash = sha256_file(registration_path)
    if not args.audio:
        spec = next(item for item in specs if item["leg"] == args.leg)
        folder = root / "experiments" / spec["experiment_id"]
        capture_path = folder / "capture.wav"
        artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
        output = folder / "hardware-recapture-results-001.json"
        validate_outputs(
            [output], [registration_path, source_path, capture_path, artifact_path], False
        )
        capture_hash = sha256_file(capture_path)
        forbidden = {
            registration["source_capture_sha256"],
            *(item["restore_wav_sha256"] for item in specs),
        }
        for item in specs:
            other_capture = root / "experiments" / item["experiment_id"] / "capture.wav"
            if item["leg"] != args.leg and other_capture.exists():
                forbidden.add(sha256_file(other_capture))
        recorded = load_artifact(artifact_path)
        if recorded.metadata["source_sha256"] != capture_hash or capture_hash in forbidden:
            raise ValueError("Independent NEW first-pair capture identity differs")
        base, target, actual = [
            decode_artifact(item)
            for item in (
                load_artifact(source_path),
                load_artifact(folder / "edited.symbols.npz"),
                recorded,
            )
        ]
        checks = reception_checks(base, target, actual, spec)
        write_bytes(
            output,
            json_bytes(
                {
                    "analysis_version": "first-pair-FX-exact-native-recapture-check-0.1",
                    "hardware_verified": False,
                    "passed": all(checks.values()),
                    "checks": checks,
                    "leg": args.leg,
                    "registration_sha256": registration_hash,
                    "capture_sha256": capture_hash,
                    "artifact_sha256": sha256_file(artifact_path),
                    "artifact_path": artifact_path.relative_to(root).as_posix(),
                    "native_frame": frame_report(actual),
                    "audible_effect_order_evaluated": False,
                    "general_per_step_FX_writer_enabled": False,
                    "limits": registration["limits"],
                }
            ),
        )
        if not all(checks.values()):
            raise ValueError("First-pair reception differs; failed report retained")
        return
    folders = [root / "experiments" / spec["experiment_id"] for spec in specs]
    paths = [folder / "playback.wav" for folder in folders]
    measurements = [folder / "first-tone-results-001.json" for folder in folders]
    native_paths = [folder / "hardware-recapture-results-001.json" for folder in folders]
    output = root / "experiments/pattern1-FX-first-pair-audio-comparison-001.json"
    validate_outputs([output, *measurements], [registration_path, *paths, *native_paths], False)
    for folder, path in zip(folders, native_paths):
        require_native_result(
            json.loads(path.read_text()),
            registration_hash,
            sha256_file(folder / "capture.wav"),
            sha256_file(folder / "derived/analysis-001/capture.symbols.npz"),
        )
    if sha256_file(paths[0]) == sha256_file(paths[1]):
        raise ValueError("Two independent ordinary playback WAVs required")
    reports = [audio_report(path, PARAMETERS) for path in paths]
    for path, report in zip(measurements, reports):
        write_bytes(path, json_bytes(report))
    comparison = compare_audio(*reports, PARAMETERS)
    comparison.update(
        analysis_version="frozen-first-tone-complementary-FX-nibble-order-comparison-0.1",
        registration_sha256=registration_hash,
        audio_results_sha256=[sha256_file(path) for path in measurements],
        native_results_sha256=[sha256_file(path) for path in native_paths],
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(comparison))
    if not comparison["comparison_usable"]:
        raise ValueError("First-tone comparison unusable; unchanged-method reports retained")


if __name__ == "__main__":
    main()
