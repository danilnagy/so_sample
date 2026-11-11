"""Compare frozen interior volume encodings and enable-bit alternatives without refitting."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_volume_lock_range import comparison_checks
from scripts.check_sound3_volume_probe import raw_changes
from scripts.prepare_sound3_volume_middle_series import CAPTURE_IDS


def raw_components(frame):
    data = pattern_data(frame, 1)
    return [(data[48 * step + 6] >> 6, data[48 * step + 7] & 15) for step in range(16)]


def broad_preservation(before, after):
    # Reuse every narrow-control check except the explicitly falsified mask rule.
    controls = comparison_checks(before, after, [48 * step + 7 for step in range(16)])
    del controls["all_pattern1_bits_except_candidate_low_nibbles_unchanged"]
    masked = []
    for frame in (before, after):
        data = bytearray(pattern_data(frame, 1))
        for step in range(16):
            data[48 * step + 6] &= 0x3F
            data[48 * step + 7] &= 0xF0
        masked.append(data)
    controls["all_pattern1_bits_outside_both_candidate_masks_unchanged"] = masked[0] == masked[1]
    return controls


def series_checks(base, minimum, frames, registration):
    if len(frames) != 3 or len(registration["expected_capture_sequence"]) != 3:
        raise ValueError("Exactly quarter,middle and maximum-return captures required")
    candidate = registration["candidate"]
    if (
        candidate["pattern"],
        candidate["sound"],
        candidate["first_primary_byte_mask"],
        candidate["second_primary_byte_mask"],
    ) != (1, 3, 192, 15) or candidate["steps"] != list(range(1, 17)):
        raise ValueError(
            "Exactly the two preregistered masks for all16 Pattern1 Sound3 cells required"
        )
    scopes, differences = [], []
    previous = base
    for frame in frames:
        scopes.append(broad_preservation(previous, frame))
        differences.append(raw_changes(previous, frame))
        previous = frame
    endpoint_scope = broad_preservation(base, minimum)
    controls = {
        "source_maximum_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["baseline_body_sha256"],
        "all_actual_bodies_reencode_exactly": all(
            encode_packets(frame.packets) == frame.encoded_body for frame in (minimum, *frames)
        ),
        "independent_minimum_differs_only_in_new_broader_mask": all(endpoint_scope.values()),
    }
    returns = {
        "complete_return_body_equals_independent_maximum": frames[-1].encoded_body
        == base.encoded_body,
        "complete_return_packets_equal_independent_maximum": frames[-1].packets == base.packets,
        "return_entire_body_matches_preregistered_prediction": hashlib.sha256(
            frames[-1].encoded_body
        ).hexdigest()
        == registration["expected_capture_sequence"][-1]["expected_body_sha256"],
    }
    components = [raw_components(frame) for frame in (minimum, frames[0], frames[1], frames[2])]
    all_scope = (
        all(controls.values())
        and all(all(scope.values()) for scope in scopes)
        and all(returns.values())
    )
    models = {}
    for name, decode in (
        ("contiguous_little_endian_six_bit_value", lambda pair: pair[0] | (pair[1] << 2)),
        ("two_first_byte_bits_are_most_significant", lambda pair: (pair[0] << 4) | pair[1]),
    ):
        values = [[decode(pair) for pair in capture] for capture in components]
        uniform = all(len(set(capture)) == 1 for capture in values)
        q, m = values[1][0], values[2][0]
        order = uniform and values[0] == [0] * 16 and values[-1] == [63] * 16 and 0 < q < m < 63
        quarter_band, middle_band = [
            registration["position_hypotheses"][name]
            for name in ("quarter_raw_six_bit_band", "middle_raw_six_bit_band")
        ]
        bands = (
            uniform
            and quarter_band[0] <= q <= quarter_band[1]
            and middle_band[0] <= m <= middle_band[1]
        )
        models[name] = {
            "raw_values_minimum_quarter_middle_return": values,
            "all16_cells_uniform_at_each_position": uniform,
            "minimum_quarter_middle_maximum_strict_order": order,
            "auxiliary_mechanical_position_bands_match": bands,
            "field_scope_and_relative_order_supported": all_scope and order,
        }
    flags = all(
        first == (3 if second else 0) for capture in components for first, second in capture
    )
    primary = [(first << 6, second) for capture in components[1:3] for first, second in capture]
    return {
        "control_checks": controls,
        "control_passed": all(controls.values()),
        "leg_preservation_checks": scopes,
        "return_hypotheses": returns,
        "all_field_scope_and_return_checks_pass": all_scope,
        "encoding_models": models,
        "four_bit_value_with_zero_nonzero_enable_pair": {
            "all_recorded_nonzero_values_have_c0_and_zero_values_have00": flags,
            "supported_with_preservation": all_scope and flags,
        },
        "interior_has_first_byte_pair01_or10": any(first in (64, 128) for first, _ in primary),
        "leg_raw_changes_against_actual_preceding_capture": differences,
        "candidate_model_preferences_from_auxiliary_position_bands": [
            name
            for name, model in models.items()
            if model["field_scope_and_relative_order_supported"]
            and model["auxiliary_mechanical_position_bands_match"]
        ],
        "numeric_display_values_inferred": False,
        "gain_curve_or_packed_order_definitively_confirmed": False,
        "volume_writer_enabled": False,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, nargs=3)
    parser.add_argument("--display-texts", nargs=3)
    args = parser.parse_args()
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    captures = [directory / "capture.wav" for directory in directories]
    paths = args.artifacts or [
        directory / "derived/analysis-001/capture.symbols.npz" for directory in directories
    ]
    registration_path = root / "experiments/sound3-volume-middle-series-registration-001.json"
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["baseline_artifact"]
    minimum_path = root / registration["minimum_endpoint_artifact"]
    output = root / "experiments/sound3-volume-middle-series-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, minimum_path, *captures, *paths], False
    )
    recorded = [load_artifact(path) for path in paths]
    if (
        sha256_file(source_path) != registration["baseline_artifact_sha256"]
        or sha256_file(root / registration["baseline_capture"])
        != registration["baseline_capture_sha256"]
        or sha256_file(minimum_path) != registration["minimum_endpoint_artifact_sha256"]
        or sha256_file(root / "experiments/sound3-volume-lock-range-results-001.json")
        != registration["failed_four_bit_results_sha256"]
        or any(
            item.metadata["source_sha256"] != sha256_file(capture)
            for item, capture in zip(recorded, captures)
        )
    ):
        raise ValueError("Registered endpoint,falsified model or interior capture identity differs")
    base, minimum = [decode_artifact(load_artifact(path)) for path in (source_path, minimum_path)]
    frames = [decode_artifact(item) for item in recorded]
    report = series_checks(base, minimum, frames, registration)
    report.update(
        analysis_version="sound3-interior-packed-value-and-enable-alternative-check-0.1",
        hardware_verified=False,
        registration_sha256=sha256_file(registration_path),
        independently_reported_display_texts=args.display_texts,
        captures=[
            {
                "experiment_id": directory.name,
                "capture_sha256": sha256_file(capture),
                "artifact_sha256": sha256_file(path),
                "artifact_path": str(path),
                "native_frame": frame_report(frame),
            }
            for directory, capture, path, frame in zip(directories, captures, paths, frames)
        ],
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if not report["control_passed"]:
        raise ValueError("Interior source or native controls failed; report retained")


if __name__ == "__main__":
    main()
