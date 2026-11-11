"""Retain no-change, narrow/wide third-byte and coupled FILTER B alternatives."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_probe import recorded_report
from scripts.prepare_sound3_filter_B_probe import CAPTURE_ID, REGISTRATION


def B_probe_report(base, actual, registration):
    if registration["B_candidate_masks"] != {
        "third_primary_bits2_to6": 124,
        "third_primary_bits2_to7": 252,
    }:
        raise ValueError("FILTER B masks differ from fixed preregistered alternatives")
    context = recorded_report(base, actual, registration)
    before, after = [pattern_data(frame, 1) for frame in (base, actual)]
    preserve = all(context["preservation_checks"].values())
    cells = context["changed_cells"]
    only_sound3 = bool(cells) and preserve and all(cell["sound_slot"] == 3 for cell in cells)
    aux_exact = all(cell["auxiliary_before"] == cell["auxiliary_after"] for cell in cells)

    def matches_except(second_mask, third_mask):
        a, b = bytearray(before), bytearray(after)
        for data in (a, b):
            for step in range(16):
                data[48 * step + 7] &= 255 ^ second_mask
                data[48 * step + 8] &= 255 ^ third_mask
        return preserve and a == b

    mask_reports = {}
    for name, mask in registration["B_candidate_masks"].items():
        changes = [
            step + 1
            for step in range(16)
            if before[48 * step + 8] & mask != after[48 * step + 8] & mask
        ]
        mask_reports[name] = {
            "changed_steps": changes,
            "only_candidate_bits_and_all_other_state_preserved": matches_except(0, mask),
            "changed_only_within_candidate_supported": bool(changes) and matches_except(0, mask),
        }
    projections = {
        name: {
            "third_bits2_to6_values": [(data[48 * step + 8] >> 2) & 31 for step in range(16)],
            "third_bits2_to7_values": [data[48 * step + 8] >> 2 for step in range(16)],
            "third_bit7_values": [data[48 * step + 8] >> 7 for step in range(16)],
        }
        for name, data in (("before", before), ("after", after))
    }
    fields = context["raw_Sound3_fields"]["after"]
    return {
        "source_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "actual_native_controls_pass": all(context["native_checks"].values()),
        "no_serialized_change": actual.encoded_body == base.encoded_body,
        "B_candidate_mask_reports": mask_reports,
        "broader_FILTER_snapshot_supported": only_sound3 and aux_exact and matches_except(240, 255),
        "other_Sound3_primary_changes_supported": only_sound3 and aux_exact,
        "Sound3_primary_and_auxiliary_changes_supported": only_sound3,
        "pitch14_and_volume36_preserved": fields["first_low5_values"]
        == registration["expected_pitch_values"]
        and fields["volume_values"] == registration["expected_volume_values"],
        "filter_A63_preserved": fields["uninterpreted_candidate_values"]
        == registration["expected_filter_A_values"],
        "raw_B_candidate_projections": projections,
        "after_projection_uniformity": {
            name: len(set(values)) == 1 for name, values in projections["after"].items()
        },
        "filter_A_context_report": context,
        "B_endpoint_guessed": False,
        "resonance_field_width_scale_or_bit7_role_confirmed": False,
        "resonance_writer_enabled": False,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    folder = root / "experiments" / CAPTURE_ID
    source_path = root / registration["source_artifact"]
    capture_path = folder / "capture.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    observation_path = (
        root / "experiments/edited-sound3-filter63-center-001/hardware-observation-001.json"
    )
    output = folder / "B-probe-results-001.json"
    validate_outputs([output], [registration_path, source_path, capture_path, artifact_path], False)
    recorded = load_artifact(artifact_path)
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
        or sha256_file(observation_path) != registration["source_observation_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture_path)
    ):
        raise ValueError("Registered neutral source or independent B capture identity differs")
    actual = decode_artifact(recorded)
    report = B_probe_report(decode_artifact(load_artifact(source_path)), actual, registration)
    report.update(
        analysis_version="recorded-FILTER-B-third-byte-location-check-0.1",
        hardware_verified=False,
        registration_sha256=sha256_file(registration_path),
        capture_sha256=sha256_file(capture_path),
        artifact_sha256=sha256_file(artifact_path),
        artifact_path=artifact_path.relative_to(root).as_posix(),
        native_frame=frame_report(actual),
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if not report["source_body_matches_registration"] or not report["actual_native_controls_pass"]:
        raise ValueError("FILTER B native control failed; report retained")


if __name__ == "__main__":
    main()
