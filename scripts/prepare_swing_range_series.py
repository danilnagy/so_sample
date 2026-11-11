"""Register unknown swing minimum, displayed9 and exactS18 return before collection."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import Packet, decode_artifact, encode_packets
from po33_re.modem.symbols import load_artifact

CAPTURE_IDS = ("event-038-b-swing-minimum", "event-039-c-swing-9", "event-040-a-return-swing18")


def main():
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    if any(path.exists() or path.is_symlink() for path in directories):
        raise ValueError("All three capture directories must be fresh")
    baseline = root / "experiments/event-037-b-swing-maximum"
    observation_path = baseline / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    original_reg = json.loads((baseline / "swing-registration.json").read_text())
    source_path = root / observation["artifact_path"]
    zero_path = root / original_reg["baseline_artifact"]
    registration_path = root / "experiments/swing-range-series-registration-001.json"
    validate_outputs(
        [registration_path],
        [observation_path, source_path, zero_path, baseline / "capture.wav"],
        False,
    )
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or observation["display_text"] != "S18"
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != observation["capture_sha256"]
        or sha256_file(zero_path) != original_reg["baseline_artifact_sha256"]
    ):
        raise ValueError("Unchanged maximumS18 and original zero-byte evidence required")
    base, zero = [decode_artifact(load_artifact(path)) for path in (source_path, zero_path)]
    if hashlib.sha256(base.encoded_body).hexdigest() != observation["body_sha256"] or base.packets[
        2
    ].payload[129:131] != bytes([137, 18]):
        raise ValueError("Expected137 tempo and independently observed18 candidate")
    middle_packets = list(base.packets)
    old = middle_packets[2].payload
    middle_packets[2] = Packet(0x7D5C, old[:130] + b"\x09" + old[131:])
    middle_body = encode_packets(middle_packets)
    registration = {
        "analysis_version": "swing-minimum-middle9-and-exact18-return-preregistration-0.1",
        "registered_before_all_captures": True,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": observation["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_capture_sha256": observation["capture_sha256"],
        "baseline_body_sha256": observation["body_sha256"],
        "baseline_observation_sha256": sha256_file(observation_path),
        "original_zero_artifact": zero_path.relative_to(root).as_posix(),
        "original_zero_artifact_sha256": sha256_file(zero_path),
        "original_zero_body_sha256": hashlib.sha256(zero.encoded_body).hexdigest(),
        "expected_tempo_bpm": 137,
        "candidate": {
            "tag": "0x7d5c",
            "occurrence_index_zero_based": 1,
            "payload_offset_zero_based": 130,
            "baseline_encoded_value": 18,
        },
        "expected_capture_sequence": [
            {
                "experiment_id": CAPTURE_IDS[0],
                "action": "Hold BPM and turn A fully counterclockwise",
                "requested_display_value": None,
                "expected_body_sha256": None,
            },
            {
                "experiment_id": CAPTURE_IDS[1],
                "action": "Hold BPM and set displayed swing9",
                "requested_display_value": 9,
                "expected_body_sha256": hashlib.sha256(middle_body).hexdigest(),
            },
            {
                "experiment_id": CAPTURE_IDS[2],
                "action": "Hold BPM and return to displayed maximum18",
                "requested_display_value": 18,
                "expected_body_sha256": observation["body_sha256"],
            },
        ],
        "encoding_models": {
            "direct_unsigned_byte": "Every independently reported numeric display equals the raw byte130",
            "direct_signed_byte": "Every independently reported numeric display equals signed8(raw byte130), with bytes>=128 interpreted as byte-256",
            "minimum_value_is_unknown": True,
            "minimum_zero_returns_prior_zero_body": "Conditional only: if user independently observes minimum0, that capture must equal the complete independent original zero-byte state",
        },
        "limits": [
            "Unsigned and signed8 models are registered before minimum data; no after-the-fact scale or offset fitting",
            "No minimum number, percentage or timing unit is assumed",
            "Middle9 and return18 must match their complete body predictions; return must equal originalS18 state",
            "Missing display readings remain unevaluated; no swing writer is enabled",
        ],
    }
    for directory, expected in zip(directories, registration["expected_capture_sequence"]):
        directory.mkdir()
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_swing_minimum_middle_or_return",
                    "expected_file": "capture.wav",
                    "series_registration": "../swing-range-series-registration-001.json",
                    "requested_display_value": expected["requested_display_value"],
                    "planned_actions": [
                        "Keep Pattern1/Sound8/TONE stopped/write off, tempo137 and knob B unchanged",
                        expected["action"] + "; stop moving A before releasing BPM",
                        "Before playback save complete stereo capture.wav at established reduced levels with one second trailing silence",
                        "Report the actual display text/value, including any minus sign, before proceeding if a requested value is unavailable",
                    ],
                }
            ),
        )
    write_bytes(directories[1] / "predicted-native-body.bin", middle_body)
    write_bytes(directories[2] / "expected-return-native-body.bin", base.encoded_body)
    write_bytes(registration_path, json_bytes(registration))
    print(
        json.dumps(
            {
                "registered": True,
                "minimum_value": "unknown",
                "middle9_body_sha256": registration["expected_capture_sequence"][1][
                    "expected_body_sha256"
                ],
                "return18_body_sha256": observation["body_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
