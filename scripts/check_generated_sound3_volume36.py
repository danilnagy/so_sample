"""Check fixed36 reception and reciprocal gain using independently decoded captures."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_sound3_volume18_restore import restore_checks
from scripts.prepare_generated_sound3_volume36 import DIRECTORY, REGISTRATION
from scripts.sound3_volume_gain_analysis import compare_reports


def evaluate_gain(reference, candidate, method):
    """Predictions reverse the original18 pair; measurement parameters stay frozen."""
    original = compare_reports(reference, candidate, method)
    rows = []
    margin = method["parameters"]["minimum_relative_amplitude_difference"]
    for item in original["measurements"]:
        row = {k: v for k, v in item.items() if not k.endswith("gain_direction_supported")}
        ratio = row["amplitude_ratio_candidate_to_reference"]
        valid = row["comparison_consistent"] and ratio is not None
        row.update(
            contiguous36_gain_direction_supported=valid and ratio > 1 + margin,
            alternative9_gain_direction_supported=valid and ratio < 1 - margin,
        )
        rows.append(row)
    return {
        "hardware_verified": False,
        "measurements": rows,
        "all_contiguous36_gain_directions_supported": all(
            row["contiguous36_gain_direction_supported"] for row in rows
        ),
        "all_alternative9_gain_directions_supported": all(
            row["alternative9_gain_direction_supported"] for row in rows
        ),
        "gain_curve_or_numeric_UI_scale_confirmed": False,
        "volume_writer_enabled": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gain", action="store_true", help="Compare audio after independent native check"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    leg = registration["expected_capture_sequence"][1]
    source_path = root / registration["source_artifact"]
    target_path = directory / "edited.symbols.npz"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    capture_path = directory / "capture.wav"
    recorded = load_artifact(artifact_path)
    method_path = root / registration["gain_measurement_registration"]
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
        or sha256_file(target_path) != leg["edited_artifact_sha256"]
        or sha256_file(directory / "restore.wav") != leg["restore_wav_sha256"]
        or sha256_file(directory / "software-validation.json") != leg["software_validation_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture_path)
        or sha256_file(method_path) != registration["gain_measurement_registration_sha256"]
    ):
        raise ValueError("Registered source,target,method or recapture identity differs")
    source, target, actual = [
        decode_artifact(item)
        for item in (load_artifact(source_path), load_artifact(target_path), recorded)
    ]
    checks = restore_checks(source, target, actual, leg, registration)
    native_path = directory / "hardware-recapture-results-001.json"
    if not args.gain:
        validate_outputs([native_path], [registration_path, artifact_path, capture_path], False)
        write_bytes(
            native_path,
            json_bytes(
                {
                    "analysis_version": "fixed-volume36-native-recapture-check-0.1",
                    "hardware_verified": False,
                    "passed": all(checks.values()),
                    "checks": checks,
                    "registration_sha256": sha256_file(registration_path),
                    "capture_sha256": sha256_file(capture_path),
                    "artifact_sha256": sha256_file(artifact_path),
                    "artifact_path": artifact_path.relative_to(root).as_posix(),
                    "native_frame": frame_report(actual),
                    "audible_gain_evaluated": False,
                    "volume_writer_enabled": False,
                    "limits": registration["limits"],
                }
            ),
        )
        if not all(checks.values()):
            raise ValueError("Recapture differs from fixed36 target; report retained")
        return
    native = json.loads(native_path.read_text())
    reference = (root / registration["reference_audio"]).parent
    reference_native_path = reference / "hardware-recapture-results-001.json"
    reference_native = json.loads(reference_native_path.read_text())
    paths = [path / "playback-gain-results-001.json" for path in (reference, directory)]
    reports = [json.loads(path.read_text()) for path in paths]
    method = json.loads(method_path.read_text())
    if (
        not all(checks.values())
        or not native["passed"]
        or not reference_native["passed"]
        or native["registration_sha256"] != sha256_file(registration_path)
        or native["capture_sha256"] != sha256_file(capture_path)
        or native["artifact_sha256"] != sha256_file(artifact_path)
        or reference_native["capture_sha256"] != sha256_file(root / registration["source_capture"])
        or reference_native["artifact_sha256"] != sha256_file(source_path)
        or sha256_file(reference / "playback.wav") != registration["reference_audio_sha256"]
        or sha256_file(paths[0]) != registration["reference_audio_results_sha256"]
        or any(
            report["source_sha256"] != sha256_file(path / "playback.wav")
            or report["registration_sha256"] != sha256_file(method_path)
            for path, report in zip((reference, directory), reports)
        )
    ):
        raise ValueError("Native and frozen audio inputs do not match")
    output = root / "experiments/sound3-generated-volume36-gain-results-001.json"
    validate_outputs([output], [registration_path, method_path, *paths, native_path], False)
    result = evaluate_gain(*reports, method)
    result.update(
        analysis_version="fixed-volume36-reciprocal-gain-comparison-0.1",
        registration_sha256=sha256_file(registration_path),
        gain_method_sha256=sha256_file(method_path),
        gain_input_reports_sha256=[sha256_file(path) for path in paths],
        native_input_reports_sha256=[
            sha256_file(path) for path in (reference_native_path, native_path)
        ],
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(result))
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "all_contiguous36_gain_directions_supported",
                    "all_alternative9_gain_directions_supported",
                    "hardware_verified",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
