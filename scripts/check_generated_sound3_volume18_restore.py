"""Check reference21 or candidate18 native reception independently of audible gain."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_volume_middle_series import broad_preservation
from scripts.prepare_generated_sound3_volume18_pair import DIRECTORIES


def restore_checks(source, target, actual, leg, registration):
    data = pattern_data(actual, 1)
    values = [(data[48 * step + 6] >> 6) | ((data[48 * step + 7] & 15) << 2) for step in range(16)]
    return dict(
        broad_preservation(source, actual),
        source_body_matches_registration=hashlib.sha256(source.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        supplied_target_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == leg["expected_body_sha256"],
        entire_recapture_body_matches_target=actual.encoded_body == target.encoded_body,
        entire_recapture_packets_match_target=actual.packets == target.packets,
        all16_candidate_fields_equal_registered_raw_code=values
        == [leg["contiguous_raw_code"]] * 16,
        expected_native_geometry=len(actual.packets) == 815 and actual.end_byte == 156758,
    )


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leg", choices=("reference", "candidate"), required=True)
    parser.add_argument("--artifact", type=Path)
    args = parser.parse_args()
    index = ("reference", "candidate").index(args.leg)
    directory = root / "experiments" / DIRECTORIES[index]
    registration_path = root / "experiments/sound3-generated-volume18-pair-registration-001.json"
    registration = json.loads(registration_path.read_text())
    leg = registration["expected_capture_sequence"][index]
    source_path = root / registration["source_artifact"]
    target_path = directory / "edited.symbols.npz"
    artifact_path = args.artifact or directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    output = directory / "hardware-recapture-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, target_path, artifact_path, capture], False
    )
    recorded = load_artifact(artifact_path)
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
        or sha256_file(target_path) != leg["edited_artifact_sha256"]
        or sha256_file(directory / "restore.wav") != leg["restore_wav_sha256"]
        or sha256_file(directory / "software-validation.json") != leg["software_validation_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Registered volume source,generated target or recapture identity differs")
    source, target, actual = [
        decode_artifact(item)
        for item in (load_artifact(source_path), load_artifact(target_path), recorded)
    ]
    checks = restore_checks(source, target, actual, leg, registration)
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "generated-volume-reference-or-probe-recapture-check-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "passed": all(checks.values()),
                "checks": checks,
                "capture_sha256": sha256_file(capture),
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
        raise ValueError(
            "Volume recapture differs from registered complete target; report retained"
        )


if __name__ == "__main__":
    main()
