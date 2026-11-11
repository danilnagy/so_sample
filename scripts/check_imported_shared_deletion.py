"""Check the physical shared-owner deletion at the imported endpoint."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_shared_sound6_deletion import comparison_checks


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-028-b-delete-imported-shared-sound6"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact", type=Path, default=directory / "derived/analysis-001/capture.symbols.npz"
    )
    args = parser.parse_args()
    registration_path = directory / "deletion-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["baseline_artifact"]
    baseline_capture = root / registration["baseline_capture"]
    capture = directory / "capture.wav"
    output = directory / "hardware-recapture-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, baseline_capture, capture, args.artifact], False
    )
    source, recorded = load_artifact(source_path), load_artifact(args.artifact)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(baseline_capture) != registration["baseline_source_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
        or sha256_file(directory / "predicted-native-body.bin")
        != registration["predicted_body_file_sha256"]
    ):
        raise ValueError("Registered source or recapture identity differs")
    base, actual = decode_artifact(source), decode_artifact(recorded)
    if hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]:
        raise ValueError("Registered source body differs")
    checks, fits, changed, records, observed = comparison_checks(base, actual, registration)
    report = {
        "analysis_version": "physical-imported-shared-deletion-recapture-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(args.artifact),
        "artifact_path": str(args.artifact),
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "changed_selector_ids": changed,
        "changed_sound_records": records,
        "observed_ownership": observed,
        "native_frame": frame_report(actual),
        "limits": registration["limits"],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Imported shared deletion control failed; report retained")


if __name__ == "__main__":
    main()
