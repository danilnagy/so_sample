"""Preregister the fine-tempo endpoints and complete return before three captures."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo_control import comparison_checks

CAPTURE_IDS = (
    "event-034-b-fine-tempo-60",
    "event-035-c-fine-tempo-240",
    "event-036-a-return-fine-tempo-100",
)
EXPECTED_BPMS = (60, 240, 100)
ORIGINAL100_BODY = "d01d2cdd2f9cd85aca19e17ebc7967327aba647926faf91dcb2db0fe42de2633"


def predict_range_frames(base):
    """Research predictions only for the fixed three-leg sequence from known100."""
    if hashlib.sha256(base.encoded_body).hexdigest() != ORIGINAL100_BODY:
        raise ValueError("Exact independently observed fine100 state required")
    predictions = []
    old = base.packets[2].payload
    for bpm in EXPECTED_BPMS:
        packets = list(base.packets)
        packets[2] = Packet(0x7D5C, old[:129] + bytes([bpm]) + old[130:])
        predictions.append(decode_frame(bytes(4095) + encode_packets(packets)))
    return tuple(predictions)


def main():
    root = Path(__file__).resolve().parents[1]
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    if any(path.exists() or path.is_symlink() for path in directories):
        raise ValueError("All three capture directories must be fresh")
    registration_path = root / "experiments/fine-tempo-range-series-registration-001.json"
    validation_path = root / "experiments/fine-tempo-range-series-prediction-checks-001.json"
    baseline = root / "experiments/event-033-b-fine-tempo-100"
    observation_path = baseline / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    validate_outputs(
        [registration_path, validation_path],
        [observation_path, source_path, baseline / "capture.wav"],
        False,
    )
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or observation["display_bpm"] != 100
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Unchanged physically observed fine100 source required")
    base = decode_artifact(load_artifact(source_path))
    if hashlib.sha256(base.encoded_body).hexdigest() != observation["body_sha256"]:
        raise ValueError("Observed fine100 body differs")
    predictions = predict_range_frames(base)
    registration = {
        "analysis_version": "fine-tempo-endpoints-and-exact100-return-preregistration-0.1",
        "registered_before_all_captures": True,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": observation["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_capture_sha256": observation["capture_sha256"],
        "baseline_body_sha256": observation["body_sha256"],
        "baseline_observation_sha256": sha256_file(observation_path),
        "expected_initial_display_bpm": 100,
        "candidate": {
            "tag": "0x7d5c",
            "occurrence_index_zero_based": 1,
            "payload_offset_zero_based": 129,
            "baseline_encoded_value": 100,
            "hypothesis": "Fine minimum60 and maximum240 use the same direct unsigned byte; return100 recovers the entire original fine100 body",
        },
        "expected_capture_sequence": [
            {
                "experiment_id": name,
                "expected_before_bpm": prior,
                "expected_after_bpm": bpm,
                "expected_body_sha256": hashlib.sha256(frame.encoded_body).hexdigest(),
            }
            for name, prior, bpm, frame in zip(
                CAPTURE_IDS, (100, 60, 240), EXPECTED_BPMS, predictions
            )
        ],
        "official_reference": {
            "url": "https://teenage.engineering/guides/po-33/en",
            "reviewed_date": "2026-10-09",
            "section": "6, tempo",
            "paraphrase": "Fine tempo uses BPM held with knob B and spans60 to240; knob A adjusts swing and is excluded",
        },
        "limits": [
            "Expected display readings must be independently observed; never inferred from candidate bytes",
            "No public fine-tempo range is enabled and no generated fine-tempo restore is claimed",
            "Each leg is compared with the actual preceding capture; predicted body equality remains separate",
            "Only the fixed byte model is tested; extra global/slot-parameter changes and incomplete return remain visible",
        ],
    }
    previous, previous_bpm = base, 100
    checks = {}
    for number, (predicted, bpm) in enumerate(zip(predictions, EXPECTED_BPMS), 1):
        leg_reg = dict(
            registration, baseline_body_sha256=hashlib.sha256(previous.encoded_body).hexdigest()
        )
        controls, fits, _ = comparison_checks(previous, predicted, leg_reg, previous_bpm, bpm)
        checks[f"leg{number}_synthetic_controls_and_hypotheses"] = all(controls.values()) and all(
            fits.values()
        )
        previous, previous_bpm = predicted, bpm
    checks["complete_return_equals_independently_observed100_body"] = (
        predictions[-1].encoded_body == base.encoded_body
    )
    assert all(checks.values()), checks
    for directory, frame, expected in zip(
        directories, predictions, registration["expected_capture_sequence"]
    ):
        directory.mkdir()
        write_bytes(directory / "predicted-native-body.bin", frame.encoded_body)
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_fine_tempo_endpoint_or_return_capture",
                    "expected_file": "capture.wav",
                    "series_registration": "../fine-tempo-range-series-registration-001.json",
                    "expected_display_before_bpm": expected["expected_before_bpm"],
                    "expected_display_after_bpm": expected["expected_after_bpm"],
                    "planned_actions": [
                        "Keep Pattern1/Sound8/TONE stopped/write off and knob A untouched",
                        f"Hold BPM continuously while turning knob B to displayed{expected['expected_after_bpm']}; stop moving B before releasing BPM",
                        "Before playback save a complete stereo capture.wav with established reduced recording levels and one second trailing silence",
                        "Report the actual display value; do not continue to the next leg without saving this capture",
                    ],
                }
            ),
        )
    write_bytes(registration_path, json_bytes(registration))
    write_bytes(
        validation_path,
        json_bytes(
            {
                "analysis_version": "fine-tempo-range-series-software-prediction-check-0.1",
                "hardware_verified": False,
                "passed": True,
                "checks": checks,
                "registration_sha256": sha256_file(registration_path),
            }
        ),
    )
    print(json.dumps({"registered": True, "sequence": registration["expected_capture_sequence"]}))


if __name__ == "__main__":
    main()
