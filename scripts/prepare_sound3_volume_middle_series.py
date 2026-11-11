"""Register interior positions to distinguish packed-six-bit and enable-flag models."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact

CAPTURE_IDS = (
    "event-047-d-sound3-volume-lock-quarter",
    "event-048-e-sound3-volume-lock-middle",
    "event-049-b-return-sound3-volume-lock-maximum",
)


def main():
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    registration_path = root / "experiments/sound3-volume-middle-series-registration-001.json"
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh registration and all three capture folders required")
    baseline = root / "experiments/event-046-b-return-sound3-tone-volume-lock-maximum"
    observation_path = baseline / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    result_path = root / "experiments/sound3-volume-lock-range-results-001.json"
    result = json.loads(result_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or observation["four_bit_only_model_supported"] is not False
        or not result["hypothesis_checks"][
            "complete_return_body_equals_independent_original_maximum"
        ]
        or result["low_nibble_minimum_and_exact_return_supported"] is not False
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Exact maximum return and preserved failed four-bit model required")
    base = decode_artifact(load_artifact(source_path))
    if base.packets[2].payload[129:131] != bytes([100, 9]):
        raise ValueError("Expected current100/swing9")
    minimum = root / "experiments/event-045-c-sound3-tone-volume-lock-minimum"
    minimum_observation_path = minimum / "hardware-observation-001.json"
    minimum_observation = json.loads(minimum_observation_path.read_text())
    minimum_path = root / minimum_observation["artifact_path"]
    if (
        not minimum_observation["hardware_verified"]
        or sha256_file(minimum_path) != minimum_observation["artifact_sha256"]
    ):
        raise ValueError("Independent minimum endpoint required")
    positions = (
        "approximately one-quarter of full travel clockwise from minimum",
        "approximately halfway between the two physical stops",
        "fully clockwise maximum",
    )
    registration = {
        "analysis_version": "sound3-quarter-middle-and-maximum-return-model-preregistration-0.1",
        "registered_before_all_captures": True,
        "hardware_verified": False,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": observation["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_capture_sha256": observation["capture_sha256"],
        "baseline_body_sha256": observation["body_sha256"],
        "baseline_observation_sha256": sha256_file(observation_path),
        "minimum_endpoint_artifact": minimum_path.relative_to(root).as_posix(),
        "minimum_endpoint_artifact_sha256": minimum_observation["artifact_sha256"],
        "minimum_endpoint_observation_sha256": sha256_file(minimum_observation_path),
        "failed_four_bit_results_sha256": sha256_file(result_path),
        "expected_tempo_bpm": 100,
        "expected_swing_byte": 9,
        "candidate": {
            "pattern": 1,
            "sound": 3,
            "steps": list(range(1, 17)),
            "first_primary_byte_mask": 192,
            "second_primary_byte_mask": 15,
            "little_endian_low16_mask": 4032,
        },
        "expected_capture_sequence": [
            {
                "experiment_id": name,
                "knobB_position": position,
                "expected_body_sha256": observation["body_sha256"] if number == 2 else None,
            }
            for number, (name, position) in enumerate(zip(CAPTURE_IDS, positions))
        ],
        "encoding_models": {
            "contiguous_little_endian_six_bit_value": "((byte0>>6)&3)|((byte1&15)<<2)",
            "two_first_byte_bits_are_most_significant": "((byte0>>6)<<4)|(byte1&15)",
            "four_bit_value_with_zero_nonzero_enable_pair": "byte1&15 is value; byte0&0xc0 must equal0xc0 whenever value is nonzero and0 when value iszero",
        },
        "position_hypotheses": {
            "quarter_raw_six_bit_band": [10, 22],
            "middle_raw_six_bit_band": [26, 38],
            "strict_relative_order": "0<quarter<middle<63",
            "position_bands_are_auxiliary": True,
        },
        "limits": [
            "The six-bit mask is a new post-endpoint hypothesis; the old four-bit-only minimum prediction remains failed and immutable",
            "Both value orderings and a four-bit-plus-enable alternative are registered before interior data",
            "Quarter/middle positions are approximate mechanical positions, not UI numbers or calibrated gain; bands are auxiliary and no exact interior body is predicted",
            "Each interior pass is expected to settle all16 Sound3 candidate fields uniformly, but deviations are reported rather than overwritten",
            "Only the two masks may change; preserve every other primary bit,auxiliary cell,sample,global and other pattern",
            "Final maximum must match the entire independent source body; no public volume writer enabled",
        ],
    }
    for directory, leg in zip(directories, registration["expected_capture_sequence"]):
        directory.mkdir()
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_recorded_volume_quarter_middle_or_maximum_return",
                    "expected_file": "capture.wav",
                    "registration": "../sound3-volume-middle-series-registration-001.json",
                    "planned_actions": [
                        "Keep Pattern1/Sound3/TONE,tempo100,swing9; knobA untouched",
                        "Play,hold WRITE and slowly turn only B to "
                        + leg["knobB_position"]
                        + " over about5 seconds",
                        "Hold WRITE3 more seconds with knobs stationary,release,stop,ensure write off,then save complete capture.wav at established reduced levels with one second tail",
                        "Save before next leg; report relative loudness and any display labels; leave final maximum stopped/write off",
                    ],
                }
            ),
        )
    write_bytes(directories[-1] / "expected-return-native-body.bin", base.encoded_body)
    write_bytes(registration_path, json_bytes(registration))
    print(
        json.dumps(
            {
                "registered": True,
                "capture_ids": CAPTURE_IDS,
                "interior_bodies_predicted": False,
                "maximum_return_sha256": observation["body_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
