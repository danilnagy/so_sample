"""Check observed third-preset and exact return captures without inferring display values."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo_control import comparison_checks


def series_checks(
    base, first, returned, original, registration, first_after_bpm=None, return_after_bpm=None
):
    controls, fits, first_observed = comparison_checks(
        base, first, registration, 140, first_after_bpm
    )
    # This is the actual first capture as the next comparison's source. Its identity
    # is reported separately; predicted first-body equality remains an independent test.
    return_reg = dict(
        registration, baseline_body_sha256=hashlib.sha256(first.encoded_body).hexdigest()
    )
    return_controls, return_fits, return_observed = comparison_checks(
        first, returned, return_reg, first_after_bpm, return_after_bpm
    )
    expected = registration["expected_capture_sequence"]
    series = {
        "first_body_equals_preregistered80_prediction": hashlib.sha256(
            first.encoded_body
        ).hexdigest()
        == expected[0]["expected_body_sha256"],
        "return_body_equals_preregistered120_prediction": hashlib.sha256(
            returned.encoded_body
        ).hexdigest()
        == expected[1]["expected_body_sha256"],
        "original120_body_matches_registration": hashlib.sha256(original.encoded_body).hexdigest()
        == registration["original120_body_sha256"],
        "entire_return_body_equals_independent_original120": returned.encoded_body
        == original.encoded_body,
        "entire_return_plain_packets_equal_independent_original120": returned.packets
        == original.packets,
        "actual_first_display_matches_registered80": first_after_bpm == 80
        if first_after_bpm is not None
        else None,
        "actual_return_display_matches_registered120": return_after_bpm == 120
        if return_after_bpm is not None
        else None,
        "first_single_byte_hypothesis_supported": first_observed["single_byte_hypothesis_status"]
        == "supported_for_this_transition",
        "return_single_byte_hypothesis_supported": return_observed["single_byte_hypothesis_status"]
        == "supported_for_this_transition",
    }
    return {
        "first_controls": controls,
        "first_hypotheses": fits,
        "first_observed": first_observed,
        "return_controls": return_controls,
        "return_hypotheses": return_fits,
        "return_observed": return_observed,
        "series_hypotheses": series,
        "control_passed": all(controls.values()) and all(return_controls.values()),
        "series_supported": all(controls.values())
        and all(return_controls.values())
        and all(value is True for value in series.values()),
    }


def main():
    root = Path(__file__).resolve().parents[1]
    first_dir = root / "experiments/event-031-b-tempo-80"
    return_dir = root / "experiments/event-032-a-return-tempo-120"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--first-artifact",
        type=Path,
        default=first_dir / "derived/analysis-001/capture.symbols.npz",
    )
    parser.add_argument(
        "--return-artifact",
        type=Path,
        default=return_dir / "derived/analysis-001/capture.symbols.npz",
    )
    parser.add_argument("--first-after-bpm", type=int)
    parser.add_argument("--return-after-bpm", type=int)
    args = parser.parse_args()
    registration_path = root / "experiments/tempo-preset-series-registration-001.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["baseline_artifact"]
    original_path = root / registration["original120_artifact"]
    output = root / "experiments/tempo-preset-series-results-001.json"
    first_capture, return_capture = first_dir / "capture.wav", return_dir / "capture.wav"
    validate_outputs(
        [output],
        [
            registration_path,
            source_path,
            original_path,
            first_capture,
            return_capture,
            args.first_artifact,
            args.return_artifact,
        ],
        False,
    )
    source, original, first, returned = [
        load_artifact(path)
        for path in (source_path, original_path, args.first_artifact, args.return_artifact)
    ]
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(root / registration["baseline_capture"])
        != registration["baseline_capture_sha256"]
        or sha256_file(original_path) != registration["original120_artifact_sha256"]
        or first.metadata["source_sha256"] != sha256_file(first_capture)
        or returned.metadata["source_sha256"] != sha256_file(return_capture)
    ):
        raise ValueError("Registered source or series capture identities differ")
    base_frame, original_frame, first_frame, return_frame = map(
        decode_artifact, (source, original, first, returned)
    )
    report = series_checks(
        base_frame,
        first_frame,
        return_frame,
        original_frame,
        registration,
        args.first_after_bpm,
        args.return_after_bpm,
    )
    report.update(
        analysis_version="tempo-third-preset-and-original-return-control-check-0.1",
        registration_sha256=sha256_file(registration_path),
        first_capture_sha256=sha256_file(first_capture),
        return_capture_sha256=sha256_file(return_capture),
        first_artifact_sha256=sha256_file(args.first_artifact),
        return_artifact_sha256=sha256_file(args.return_artifact),
        first_frame=frame_report(first_frame),
        return_frame=frame_report(return_frame),
        tempo_writer_enabled=False,
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Tempo preset series changed core invariants; report retained")


if __name__ == "__main__":
    main()
