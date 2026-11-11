"""Register a third tempo value and exact original-state return before either capture."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo_control import comparison_checks


def predict_preset(frame, bpm):
    """Research prediction only at the fixed preregistered byte; not a public writer."""
    if type(bpm) is not int or bpm not in (80, 120):
        raise ValueError("Only the registered 80 and120 preset predictions are supported")
    globals_ = [i for i, packet in enumerate(frame.packets) if packet.tag == 0x7D5C]
    if len(globals_) != 2 or any(len(frame.packets[i].payload) != 255 for i in globals_):
        raise ValueError("Two observed opaque global records required")
    index = globals_[1]
    old = frame.packets[index].payload
    if old[129] != 140:
        raise ValueError("Expected the observed 140 baseline candidate")
    packets = list(frame.packets)
    packets[index] = Packet(0x7D5C, old[:129] + bytes([bpm]) + old[130:])
    return decode_frame(bytes(4095) + encode_packets(packets))


def main():
    root = Path(__file__).resolve().parents[1]
    first_dir = root / "experiments/event-031-b-tempo-80"
    return_dir = root / "experiments/event-032-a-return-tempo-120"
    if any(path.exists() or path.is_symlink() for path in (first_dir, return_dir)):
        raise ValueError("Both capture directories must be fresh")
    registration_path = root / "experiments/tempo-preset-series-registration-001.json"
    validation_path = root / "experiments/tempo-preset-series-prediction-checks-001.json"
    observation_path = (
        root / "experiments/event-030-b-tempo-preset-once/hardware-observation-001.json"
    )
    observation = json.loads(observation_path.read_text())
    original_reg_path = root / "experiments/event-030-b-tempo-preset-once/tempo-registration.json"
    original_reg = json.loads(original_reg_path.read_text())
    source_path = root / observation["artifact_path"]
    original_path = root / original_reg["baseline_artifact"]
    source_capture = root / "experiments/event-030-b-tempo-preset-once/capture.wav"
    validate_outputs(
        [registration_path, validation_path],
        [observation_path, source_path, original_path, source_capture],
        False,
    )
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or observation["writable_field_verified"]
        or observation["tempo_writer_enabled"]
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(source_capture) != observation["capture_sha256"]
        or sha256_file(original_path) != original_reg["baseline_artifact_sha256"]
    ):
        raise ValueError(
            "Unchanged observed 140 state and independent original120 artifact required"
        )
    source = decode_artifact(load_artifact(source_path))
    original = decode_artifact(load_artifact(original_path))
    if (
        hashlib.sha256(source.encoded_body).hexdigest() != observation["body_sha256"]
        or hashlib.sha256(original.encoded_body).hexdigest() != original_reg["baseline_body_sha256"]
    ):
        raise ValueError("Pinned source bodies differ")
    first, returned = predict_preset(source, 80), predict_preset(source, 120)
    registration = {
        "analysis_version": "tempo-third-preset-and-original-return-preregistration-0.1",
        "registered_before_both_captures": True,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": observation["artifact_sha256"],
        "baseline_capture": source_capture.relative_to(root).as_posix(),
        "baseline_capture_sha256": observation["capture_sha256"],
        "baseline_body_sha256": observation["body_sha256"],
        "baseline_observation_sha256": sha256_file(observation_path),
        "original120_artifact": original_path.relative_to(root).as_posix(),
        "original120_artifact_sha256": original_reg["baseline_artifact_sha256"],
        "original120_body_sha256": original_reg["baseline_body_sha256"],
        "candidate": dict(
            original_reg["candidate"], baseline_encoded_value=140, baseline_device_display_bpm=140
        ),
        "expected_initial_display_bpm": 140,
        "expected_capture_sequence": [
            {
                "experiment_id": first_dir.name,
                "expected_before_bpm": 140,
                "expected_after_bpm": 80,
                "expected_body_sha256": hashlib.sha256(first.encoded_body).hexdigest(),
            },
            {
                "experiment_id": return_dir.name,
                "expected_before_bpm": 80,
                "expected_after_bpm": 120,
                "expected_body_sha256": original_reg["baseline_body_sha256"],
            },
        ],
        "limits": [
            "Fixed byte129 and direct integer BPM are preregistered; no offset or encoding fitting is allowed",
            "Expected preset values are predictions; actual display readings must be reported independently",
            "Returning120 must recover the complete independent original body, not only the candidate byte",
            "No tempo writer, arbitrary BPM range or hardware acceptance of generated tempo edits is established",
        ],
    }
    controls, fits, _ = comparison_checks(source, first, registration, 140, 80)
    return_reg = dict(
        registration, baseline_body_sha256=hashlib.sha256(first.encoded_body).hexdigest()
    )
    return_controls, return_fits, _ = comparison_checks(first, returned, return_reg, 80, 120)
    checks = {
        "first_prediction_passes_registered_single_byte_checks": all(controls.values())
        and all(fits.values()),
        "return_prediction_passes_registered_single_byte_checks": all(return_controls.values())
        and all(return_fits.values()),
        "return_prediction_equals_complete_independent_original_body": returned.encoded_body
        == original.encoded_body,
        "source_file_unchanged": sha256_file(source_path) == observation["artifact_sha256"],
    }
    assert all(checks.values()), checks
    first_dir.mkdir()
    return_dir.mkdir()
    write_bytes(first_dir / "predicted-native-body.bin", first.encoded_body)
    write_bytes(return_dir / "expected-return-native-body.bin", original.encoded_body)
    write_bytes(registration_path, json_bytes(registration))
    write_bytes(
        validation_path,
        json_bytes(
            {
                "analysis_version": "tempo-preset-series-software-prediction-check-0.1",
                "hardware_verified": False,
                "passed": True,
                "checks": checks,
                "registration_sha256": sha256_file(registration_path),
                "expected80_body_sha256": registration["expected_capture_sequence"][0][
                    "expected_body_sha256"
                ],
                "expected120_return_body_sha256": original_reg["baseline_body_sha256"],
            }
        ),
    )
    for directory, expected in zip(
        (first_dir, return_dir), registration["expected_capture_sequence"]
    ):
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_tempo_preset_series_capture",
                    "expected_file": "capture.wav",
                    "series_registration": "../tempo-preset-series-registration-001.json",
                    "expected_display_before_bpm": expected["expected_before_bpm"],
                    "expected_display_after_bpm": expected["expected_after_bpm"],
                    "planned_actions": [
                        "Keep Pattern1/Sound8/TONE stopped/write off and both knobs unchanged",
                        "Tap BPM once and note the displayed new BPM; report unexpected values before continuing the next leg",
                        "Before playback save complete stereo capture.wav at established reduced levels with one second trailing silence",
                        "Report the actual displayed transitions for both captures",
                    ],
                }
            ),
        )
    print(
        json.dumps(
            {
                "registered": True,
                "expected80_body_sha256": registration["expected_capture_sequence"][0][
                    "expected_body_sha256"
                ],
                "return_equals_independent120": checks[
                    "return_prediction_equals_complete_independent_original_body"
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
