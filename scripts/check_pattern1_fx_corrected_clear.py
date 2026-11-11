"""Apply the original clear prediction to corrected data, rejecting the known duplicate WAV."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_pattern1_fx_probe import fx_report
from scripts.check_pattern1_fx_return_controls import footer_global_preserved


def clear_report(base, actual, baseline, registration):
    context = fx_report(base, actual, registration)
    return {
        "source_body_matches_registration": context["source_body_matches_registration"],
        "actual_native_controls_pass": context["actual_native_controls_pass"],
        "independent_baseline_body_matches_registration": hashlib.sha256(
            baseline.encoded_body
        ).hexdigest()
        == registration["independent_no_FX_body_sha256"],
        "clear_footer_matches_original_prediction": pattern_data(actual, 1)[1024:].hex()
        == registration["expected_footer_hex"],
        "footer_plus_global_low4_scope_preserved": footer_global_preserved(base, actual, 15),
        "footer_plus_global_whole_byte_scope_preserved": footer_global_preserved(base, actual, 255),
        "clear_matches_independent_baseline_except_global131": pattern_data(actual, 1)[1024:]
        == pattern_data(baseline, 1)[1024:]
        and footer_global_preserved(baseline, actual, 255),
        "entire_clear_body_and_packets_match_baseline_diagnostic": actual.encoded_body
        == baseline.encoded_body
        and actual.packets == baseline.packets,
        "global_byte_value": actual.packets[2].payload[131],
        "literal_FX_context": context,
        "global_role_or_nibble_order_confirmed": False,
        "FX_writer_enabled": False,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments/pattern1-FX16-corrected-clear-registration-001.json"
    registration = json.loads(registration_path.read_text())
    folder = root / "experiments" / registration["experiment_id"]
    capture_path = folder / "capture.wav"
    output = folder / "corrected-clear-results-001.json"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    source_path = root / registration["source_artifact"]
    baseline_path = root / registration["independent_no_FX_artifact"]
    validate_outputs(
        [output],
        [registration_path, capture_path, artifact_path, source_path, baseline_path],
        False,
    )
    capture_hash = sha256_file(capture_path)
    if capture_hash == registration["rejected_duplicate_capture_sha256"]:
        raise ValueError(
            "Corrected clear recording is still the known duplicate FX8 WAV; cannot verify clear"
        )
    recorded = load_artifact(artifact_path)
    pins = (
        (source_path, registration["source_artifact_sha256"]),
        (root / registration["source_capture"], registration["source_capture_sha256"]),
        (
            root / "experiments/event-066-b-pattern1-FX8-recorded/hardware-observation-001.json",
            registration["source_observation_sha256"],
        ),
        (baseline_path, registration["independent_no_FX_artifact_sha256"]),
        (
            root / "experiments/pattern1-FX8-clear-return-registration-001.json",
            registration["original_clear_registration_sha256"],
        ),
        (
            root / "experiments/pattern1-FX8-clear-input-identity-observation-001.json",
            registration["input_identity_observation_sha256"],
        ),
    )
    if (
        any(sha256_file(path) != digest for path, digest in pins)
        or recorded.metadata["source_sha256"] != capture_hash
    ):
        raise ValueError("Frozen clear source/baseline or corrected capture identity differs")
    actual = decode_artifact(recorded)
    report = clear_report(
        decode_artifact(load_artifact(source_path)),
        actual,
        decode_artifact(load_artifact(baseline_path)),
        registration,
    )
    report.update(
        analysis_version="corrected-input-original-FX16-clear-prediction-check-0.1",
        hardware_verified=False,
        registration_sha256=sha256_file(registration_path),
        capture_sha256=capture_hash,
        artifact_sha256=sha256_file(artifact_path),
        artifact_path=artifact_path.relative_to(root).as_posix(),
        native_frame=frame_report(actual),
        clear_prediction_adjudicable_from_input=True,
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if (
        not report["source_body_matches_registration"]
        or not report["actual_native_controls_pass"]
        or not report["independent_baseline_body_matches_registration"]
    ):
        raise ValueError("Corrected clear native control failed; report retained")


if __name__ == "__main__":
    main()
