"""Register a low-nibble-zero minimum hypothesis and exact independent loud-state return."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact

MAXIMUM_BODY = "e34fbe7f6238c230deeacd96139b26e5ca88bb5f300a7831da87a24e32afaef7"
CAPTURE_IDS = (
    "event-045-c-sound3-tone-volume-lock-minimum",
    "event-046-b-return-sound3-tone-volume-lock-maximum",
)


def minimum_prediction_packets(frame):
    """Research prediction only: require exact independently captured loud-state source."""
    if hashlib.sha256(frame.encoded_body).hexdigest() != MAXIMUM_BODY:
        raise ValueError("Exact independently verified recorded maximum body required")
    data = bytearray(pattern_data(frame, 1))
    for step in range(16):
        offset = 48 * step + 7
        if data[offset] & 0x0F != 0x0F:
            raise ValueError("All16 candidate low nibbles must start at0xf")
        data[offset] &= 0xF0
    return _replace_pattern_data(frame, 1, bytes(data))


def main():
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    registration_path = root / "experiments/sound3-volume-lock-range-registration-001.json"
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh registration and capture directories required")
    baseline = root / "experiments/event-044-b-sound3-tone-volume-lock-up"
    observation_path = baseline / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or observation["audition_result"] != "louder"
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Verified recorded loud-state evidence required")
    base = decode_artifact(load_artifact(source_path))
    predicted_body = encode_packets(minimum_prediction_packets(base))
    registration = {
        "analysis_version": "sound3-recorded-volume-low-nibble-range-preregistration-0.1",
        "registered_before_all_captures": True,
        "hardware_verified": False,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": observation["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_capture_sha256": observation["capture_sha256"],
        "baseline_body_sha256": MAXIMUM_BODY,
        "baseline_observation_sha256": sha256_file(observation_path),
        "expected_tempo_bpm": 100,
        "expected_swing_byte": 9,
        "candidate": {
            "pattern": 1,
            "sound": 3,
            "steps": list(range(1, 17)),
            "primary_byte_index_zero_based": 1,
            "mask": 15,
            "concatenated_pattern_payload_offsets_zero_based": [
                48 * step + 7 for step in range(16)
            ],
            "raw_maximum_nibble_observed": 15,
            "raw_minimum_nibble_hypothesis": 0,
        },
        "expected_capture_sequence": [
            {
                "experiment_id": CAPTURE_IDS[0],
                "action": "Play Pattern1/Sound3/TONE; hold WRITE, move only B fully counterclockwise over about5 seconds, hold WRITE3 more seconds stationary, release,stop,ensure write off,capture",
                "expected_body_sha256": hashlib.sha256(predicted_body).hexdigest(),
            },
            {
                "experiment_id": CAPTURE_IDS[1],
                "action": "Repeat WRITE-held pass moving only B fully clockwise over about5 seconds; hold WRITE3 more seconds stationary,release,stop,ensure write off,capture",
                "expected_body_sha256": MAXIMUM_BODY,
            },
        ],
        "hypotheses": {
            "only_candidate_low_nibbles_change": "All other bits in the16 Sound3 tuples and all auxiliary/other-sound/other-pattern/sample/global bytes stay unchanged",
            "recorded_minimum_raw_nibbles_all_zero": "A falsifiable encoding hypothesis, not an assumed display value or silence",
            "recorded_maximum_return_raw_nibbles_all_f": "All16 raw nibbles match the independent original loud-state endpoint",
            "complete_return_equals_independent_maximum_body": MAXIMUM_BODY,
        },
        "limits": [
            "Initial maximum literal model was found after observing that capture; minimum and exact-return predictions are registered before new data",
            "High0xc0 bits remain opaque and must not change; no enable-flag or pitch interpretation is imposed",
            "Do not fit another scale or move the candidate if minimum0 prediction fails; report actual bytes",
            "No numeric display,percent gain,mute behavior or volume writer assumed; auditory observations remain separate",
        ],
    }
    for directory, leg in zip(directories, registration["expected_capture_sequence"]):
        directory.mkdir()
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_recorded_volume_minimum_or_exact_maximum_return",
                    "expected_file": "capture.wav",
                    "registration": "../sound3-volume-lock-range-registration-001.json",
                    "planned_actions": [
                        "Keep Pattern1/Sound3/TONE,tempo100,swing9 and knobA unchanged",
                        leg["action"],
                        "Save complete stereo backup at established reduced levels with one second trailing silence before next action",
                        "Report quieter/louder behavior and any display labels at both endpoints; leave maximum recorded and stopped/write off",
                    ],
                }
            ),
        )
    write_bytes(directories[0] / "predicted-native-body.bin", predicted_body)
    write_bytes(directories[1] / "expected-return-native-body.bin", base.encoded_body)
    write_bytes(registration_path, json_bytes(registration))
    print(
        json.dumps(
            {
                "registered": True,
                "minimum_prediction_sha256": registration["expected_capture_sequence"][0][
                    "expected_body_sha256"
                ],
                "maximum_return_sha256": MAXIMUM_BODY,
            }
        )
    )


if __name__ == "__main__":
    main()
