"""Check complete B32 reception and the frozen two-sided component-amplitude hypothesis."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.prepare_generated_sound3_resonance_middle import (
    DIRECTORY,
    REGISTRATION,
    middle_preservation_checks,
)
from scripts.sound3_pitch_frequency_analysis import audio_report
from scripts.sound3_resonance_audio import compare_resonance_audio


def middle_reception_checks(source, target, actual, registration):
    return dict(
        middle_preservation_checks(source, actual, registration),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        entire_actual_body_and_every_packet_match_target=actual.encoded_body == target.encoded_body
        and actual.packets == target.packets,
    )


def compare_middle_audio(minimum, middle, maximum, registration):
    lower = compare_resonance_audio(minimum, middle, registration)
    upper = compare_resonance_audio(middle, maximum, registration)
    return {
        "hardware_verified": False,
        "middle_above_minimum": lower,
        "maximum_above_middle": upper,
        "both_comparisons_usable": lower["comparison_usable"] and upper["comparison_usable"],
        "all_middle_amplitudes_between_endpoints_with_registered_margin": lower[
            "all_amplitude_increases_supported"
        ]
        and upper["all_amplitude_increases_supported"],
        "general_resonance_law_or_bit7_role_confirmed": False,
        "resonance_writer_enabled": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--audio",
        action="store_true",
        help="After native check, analyze playback and compare both frozen endpoints",
    )
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
    pins = (
        (source_path, registration["source_artifact_sha256"]),
        (root / registration["source_capture"], registration["source_capture_sha256"]),
        (
            root
            / "experiments/edited-sound3-filter16-B63-candidate-001/hardware-observation-001.json",
            registration["source_observation_sha256"],
        ),
        (target_path, registration["edited_artifact_sha256"]),
        (folder / "restore.wav", registration["restore_wav_sha256"]),
        (folder / "software-validation.json", registration["software_validation_sha256"]),
        (
            root / registration["original_frequency_registration"],
            registration["original_frequency_registration_sha256"],
        ),
        (
            root / "experiments/sound3-generated-filter16-B0-B63-registration-001.json",
            registration["pair_registration_sha256"],
        ),
    )
    if any(sha256_file(path) != digest for path, digest in pins):
        raise ValueError("Frozen B32 source,target or common method identity differs")
    if not args.audio:
        validate_outputs(
            [native_path],
            [registration_path, source_path, target_path, capture_path, artifact_path],
            False,
        )
        recorded = load_artifact(artifact_path)
        if recorded.metadata["source_sha256"] != sha256_file(capture_path):
            raise ValueError("Independent B32 recapture identity differs")
        source, target, actual = [
            decode_artifact(item)
            for item in (load_artifact(source_path), load_artifact(target_path), recorded)
        ]
        checks = middle_reception_checks(source, target, actual, registration)
        write_bytes(
            native_path,
            json_bytes(
                {
                    "analysis_version": "fixed-B32-native-recapture-check-0.1",
                    "hardware_verified": False,
                    "passed": all(checks.values()),
                    "checks": checks,
                    "registration_sha256": sha256_file(registration_path),
                    "capture_sha256": sha256_file(capture_path),
                    "artifact_sha256": sha256_file(artifact_path),
                    "artifact_path": artifact_path.relative_to(root).as_posix(),
                    "native_frame": frame_report(actual),
                    "audible_resonance_evaluated": False,
                    "resonance_writer_enabled": False,
                    "limits": registration["limits"],
                }
            ),
        )
        if not all(checks.values()):
            raise ValueError("B32 recapture differs from entire target; report retained")
        return
    audio_path = folder / "playback.wav"
    measurement_path = folder / "resonance-frequency-results-001.json"
    output = folder / "middle-audio-comparison-results-001.json"
    validate_outputs(
        [measurement_path, output], [registration_path, native_path, audio_path], False
    )
    native = json.loads(native_path.read_text())
    if (
        not native["passed"]
        or not all(native["checks"].values())
        or native["registration_sha256"] != sha256_file(registration_path)
        or native["capture_sha256"] != sha256_file(capture_path)
        or native["artifact_sha256"] != sha256_file(artifact_path)
    ):
        raise ValueError("Exact B32 native reception identity differs")
    endpoints = []
    for item in registration["endpoint_inputs"]:
        for path_key, sha_key in (
            ("audio_results", "audio_results_sha256"),
            ("playback", "playback_sha256"),
            ("native_results", "native_results_sha256"),
            ("capture", "capture_sha256"),
            ("artifact", "artifact_sha256"),
            ("observation", "observation_sha256"),
        ):
            if sha256_file(root / item[path_key]) != item[sha_key]:
                raise ValueError("Frozen endpoint native/audio identity differs")
        endpoints.append(json.loads((root / item["audio_results"]).read_text()))
    middle = audio_report(audio_path, registration)
    middle.update(
        registration_sha256=sha256_file(registration_path),
        native_results_sha256=sha256_file(native_path),
    )
    write_bytes(measurement_path, json_bytes(middle))
    comparison = compare_middle_audio(endpoints[0], middle, endpoints[1], registration)
    comparison.update(
        analysis_version="frozen-B32-middle-to-prior-B0-B63-component-comparison-0.1",
        registration_sha256=sha256_file(registration_path),
        middle_audio_results_sha256=sha256_file(measurement_path),
        middle_native_results_sha256=sha256_file(native_path),
        endpoint_audio_results_sha256=[
            item["audio_results_sha256"] for item in registration["endpoint_inputs"]
        ],
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(comparison))
    if not middle["passed"]:
        raise ValueError("Frozen B32 audio measurement unusable; reports retained")


if __name__ == "__main__":
    main()
