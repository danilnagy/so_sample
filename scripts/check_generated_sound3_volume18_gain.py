"""Compare native-verified reference and candidate audio with the frozen gain method."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.prepare_generated_sound3_volume18_pair import DIRECTORIES
from scripts.sound3_volume_gain_analysis import compare_reports


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    method_path = root / "experiments/sound3-volume18-gain-method-registration-001.json"
    method = json.loads(method_path.read_text())
    pair_path = root / "experiments/sound3-generated-volume18-pair-registration-001.json"
    if sha256_file(pair_path) != method["pair_registration_sha256"]:
        raise ValueError("Original generated pair differs from frozen gain method")
    directories = [root / "experiments" / name for name in DIRECTORIES]
    paths = [directory / "playback-gain-results-001.json" for directory in directories]
    output = root / "experiments/sound3-generated-volume18-gain-results-001.json"
    validate_outputs([output], [method_path, pair_path, *paths], False)
    reports = [json.loads(path.read_text()) for path in paths]
    for directory, report in zip(directories, reports):
        native_path = directory / "hardware-recapture-results-001.json"
        native = json.loads(native_path.read_text())
        if (
            not native["passed"]
            or native["capture_sha256"] != sha256_file(directory / "capture.wav")
            or native["artifact_sha256"] != sha256_file(root / native["artifact_path"])
            or report["source_sha256"] != sha256_file(directory / "playback.wav")
            or report["registration_sha256"] != sha256_file(method_path)
        ):
            raise ValueError("Independent native/audio source identities differ")
    result = compare_reports(*reports, method)
    result.update(
        analysis_version="native-verified-generated-volume18-gain-ordering-comparison-0.1",
        gain_method_sha256=sha256_file(method_path),
        pair_registration_sha256=sha256_file(pair_path),
        gain_input_reports_sha256=[sha256_file(path) for path in paths],
        native_input_reports_sha256=[
            sha256_file(directory / "hardware-recapture-results-001.json")
            for directory in directories
        ],
        volume_writer_enabled=False,
        limits=[
            "Source/settings/manual confirmations remain separate hardware observations",
            "All six channel/threshold ratios must agree in direction with unchanged pitch/loop",
            "No public volume writer or numeric UI/gain curve inferred from software",
        ],
    )
    write_bytes(output, json_bytes(result))
    print(
        json.dumps(
            {
                "contiguous_order_gain_direction_supported": result[
                    "all_contiguous_order_gain_directions_supported"
                ],
                "alternative_order_gain_direction_supported": result[
                    "all_alternative_order_gain_directions_supported"
                ],
                "hardware_verified": False,
            }
        )
    )


if __name__ == "__main__":
    main()
