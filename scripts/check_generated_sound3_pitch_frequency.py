"""Bind exact native reception and frozen independent audio before comparing pitch."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.prepare_generated_sound3_pitch_pair import DIRECTORIES, REGISTRATION
from scripts.sound3_pitch_frequency_analysis import compare_frequency_reports


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    directories = [root / "experiments" / name for name in DIRECTORIES]
    paths = [path / "pitch-frequency-results-001.json" for path in directories]
    output = root / "experiments/sound3-generated-pitch13-14-frequency-results-001.json"
    validate_outputs([output], [registration_path, *paths], False)
    reports = [json.loads(path.read_text()) for path in paths]
    native_paths = [path / "hardware-recapture-results-001.json" for path in directories]
    for directory, report, native_path in zip(directories, reports, native_paths):
        native = json.loads(native_path.read_text())
        if (
            not native["passed"]
            or not all(native["checks"].values())
            or native["registration_sha256"] != sha256_file(registration_path)
            or native["capture_sha256"] != sha256_file(directory / "capture.wav")
            or native["artifact_sha256"] != sha256_file(root / native["artifact_path"])
            or report["source_sha256"] != sha256_file(directory / "playback.wav")
            or report["registration_sha256"] != sha256_file(registration_path)
        ):
            raise ValueError("Registered exact native/audio inputs differ")
    result = compare_frequency_reports(*reports, registration["frequency_method"]["parameters"])
    result.update(
        analysis_version="native-verified-generated-pitch13-14-frequency-comparison-0.1",
        registration_sha256=sha256_file(registration_path),
        audio_input_reports_sha256=[sha256_file(path) for path in paths],
        native_input_reports_sha256=[sha256_file(path) for path in native_paths],
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(result))
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "all_frequency_increases_supported",
                    "all_one_semitone_ratios_supported",
                    "hardware_verified",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
