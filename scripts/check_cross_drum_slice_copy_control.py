"""Check the first cross-drum slice copy against its saved independent predictions."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report, sound_data
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_slice_control import reference_comparison_checks


def comparison_checks(base, frame, registration):
    # The shared helper's historical key names refer to Sound9; its comparison
    # operates on the registered selector list rather than a hard-coded slot.
    controls = dict(registration["control_checks"])
    controls["sound9_selector_ids"] = controls["destination_selector_ids"]
    checks, packets, selectors, changes, values = reference_comparison_checks(
        base, frame, {"control_checks": controls}
    )
    checks["exactly_one_sound10_reference_changed"] = checks.pop(
        "exactly_one_sound9_reference_changed"
    )
    hypotheses = registration["separately_evaluated_hypotheses"]
    copied = hypotheses["reference_copied_verbatim_from_source_key1"]
    endpoint = hypotheses["only_expected_endpoint_bytes_change"]
    fits = {
        "destination_key1_maps_to_selector24": selectors
        == hypotheses["destination_key1_maps_to_selector24"]["expected_changed_selector_ids"],
        "reference_copied_verbatim_from_source_key1": values is not None
        and values["after_hex"]
        == sound_data(base, copied["source_selector_id"]).hex()
        == copied["expected_after_hex"],
        "only_expected_endpoint_bytes_change": packets
        == endpoint["expected_changed_plain_packet_indices"]
        and changes == endpoint["expected_byte_changes"],
    }
    return checks, fits, packets, selectors, changes, values


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-019-b-copy-drum9-key1-to-drum10-key1"
    registration_path = root / "experiments/cross-drum-slice-copy-predictions-001.json"
    registration = json.loads(registration_path.read_text())
    source_path = directory / registration["baseline_artifact"]
    baseline_capture = directory / registration["baseline_capture"]
    capture = directory / "capture.wav"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    output = root / "experiments/cross-drum-slice-copy-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, baseline_capture, capture, artifact_path], False
    )
    source, recorded = load_artifact(source_path), load_artifact(artifact_path)
    base, frame = decode_artifact(source), decode_artifact(recorded)
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(baseline_capture) != registration["baseline_source_sha256"]
        or source.metadata["source_sha256"] != registration["baseline_source_sha256"]
        or hashlib.sha256(base.encoded_body).hexdigest() != registration["baseline_body_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture)
    ):
        raise ValueError("Baseline or capture differs from registered source identity")
    checks, fits, packets, selectors, changes, values = comparison_checks(base, frame, registration)
    report = {
        "analysis_version": "first-cross-drum-slice-copy-check-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "decoder_version": recorded.metadata["decoder_version"],
        "control_checks": checks,
        "control_passed": all(checks.values()),
        "hypothesis_checks": fits,
        "changed_plain_packet_indices": packets,
        "changed_selector_ids": selectors,
        "reference_byte_changes": changes,
        "reference_values": values,
        "native_frame": frame_report(frame),
        "user_report": "done",
        "limits": [
            "Sound10/key1 alone is mapped; its other15 keyboard positions remain unverified",
            "One existing owner0 reference is copied verbatim without allocation or buffer changes",
            "Tone/filter rendering and endpoint inclusivity are not established by this reference copy",
            "This is a physical copy control; a generated cross-drum restore needs separate hardware evidence",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Cross-drum slice preservation failed; report retained")


if __name__ == "__main__":
    main()
