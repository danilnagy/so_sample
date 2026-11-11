"""Require exact one-trigger reception and unchanged-method first-tone usability."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_pattern1_fx_nibble_pair import require_native_result
from scripts.pattern1_fx_nibble_audio import PARAMETERS, audio_report
from scripts.prepare_pattern1_single_tone_baseline import DIRECTORY, REGISTRATION, baseline_checks


def reception_checks(base, target, actual, registration):
    return dict(
        baseline_checks(base, actual),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        entire_actual_body_and_packets_match_target=actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    folder = root / "experiments" / DIRECTORY
    source_path = root / registration["source_artifact"]
    target_path = folder / "edited.symbols.npz"
    capture_path = folder / "capture.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    native_path = folder / "hardware-recapture-results-001.json"
    pins = [
        (source_path, registration["source_artifact_sha256"]),
        (root / registration["source_capture"], registration["source_capture_sha256"]),
        (root / registration["source_observation"], registration["source_observation_sha256"]),
        (target_path, registration["edited_artifact_sha256"]),
        (folder / "restore.wav", registration["restore_wav_sha256"]),
        (folder / "software-validation.json", registration["software_validation_sha256"]),
        (root / "scripts/pattern1_fx_nibble_audio.py", registration["audio_method_script_sha256"]),
        (
            root / "scripts/sound3_pitch_frequency_analysis.py",
            registration["frequency_fit_helper_sha256"],
        ),
        (
            root / "experiments/pattern1-FX-first-pair-audio-comparison-001.json",
            registration["earlier_inconclusive_comparison_sha256"],
        ),
    ]
    if (
        any(sha256_file(path) != digest for path, digest in pins)
        or registration["audio_parameters"] != PARAMETERS
    ):
        raise ValueError("Frozen single-tone source/target or unchanged audio method differs")
    if args.audio:
        audio_path = folder / "playback.wav"
        output = folder / "first-tone-results-001.json"
        validate_outputs([output], [registration_path, native_path, audio_path], False)
        require_native_result(
            json.loads(native_path.read_text()),
            sha256_file(registration_path),
            sha256_file(capture_path),
            sha256_file(artifact_path),
        )
        report = audio_report(audio_path, PARAMETERS)
        report.update(
            registration_sha256=sha256_file(registration_path),
            native_results_sha256=sha256_file(native_path),
            new_effect_order_adjudicated=False,
            limits=registration["limits"],
        )
        write_bytes(output, json_bytes(report))
        if not report["passed"]:
            raise ValueError("Single-tone audio unusable under unchanged method; report retained")
        return
    validate_outputs(
        [native_path],
        [registration_path, source_path, target_path, capture_path, artifact_path],
        False,
    )
    recorded = load_artifact(artifact_path)
    capture_hash = sha256_file(capture_path)
    if recorded.metadata["source_sha256"] != capture_hash or capture_hash in {
        registration["source_capture_sha256"],
        registration["restore_wav_sha256"],
    }:
        raise ValueError("Independent NEW single-tone capture identity differs")
    base, target, actual = [
        decode_artifact(item)
        for item in (load_artifact(source_path), load_artifact(target_path), recorded)
    ]
    checks = reception_checks(base, target, actual, registration)
    write_bytes(
        native_path,
        json_bytes(
            {
                "analysis_version": "single-tone-pattern-exact-native-recapture-check-0.1",
                "hardware_verified": False,
                "passed": all(checks.values()),
                "checks": checks,
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": capture_hash,
                "artifact_sha256": sha256_file(artifact_path),
                "artifact_path": artifact_path.relative_to(root).as_posix(),
                "native_frame": frame_report(actual),
                "audible_single_tone_evaluated": False,
                "general_per_step_FX_writer_enabled": False,
                "limits": registration["limits"],
            }
        ),
    )
    if not all(checks.values()):
        raise ValueError("Single-tone target reception differs; failed report retained")


if __name__ == "__main__":
    main()
