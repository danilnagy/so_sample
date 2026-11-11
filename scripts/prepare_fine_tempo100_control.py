"""Preregister a physical fine-tempo control without broadening preset editing."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.globals import calibrated_tempo_preset
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo_control import comparison_checks


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-033-b-fine-tempo-100"
    if directory.exists() or directory.is_symlink():
        raise ValueError("Fresh experiment directory required")
    baseline = root / "experiments/edited-tempo80-001"
    acceptance_path = baseline / "hardware-acceptance-001.json"
    acceptance = json.loads(acceptance_path.read_text())
    source_path = root / acceptance["artifact_path"]
    if (
        not acceptance["hardware_verified"]
        or not acceptance["writable_field_verified"]
        or not all(acceptance["checks"].values())
        or sha256_file(source_path) != acceptance["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != acceptance["capture_sha256"]
    ):
        raise ValueError("Matching hardware-accepted generated80 source required")
    base = decode_artifact(load_artifact(source_path))
    if (
        calibrated_tempo_preset(base) != 80
        or hashlib.sha256(base.encoded_body).hexdigest() != acceptance["body_sha256"]
    ):
        raise ValueError("Expected accepted80 baseline")
    packets = list(base.packets)
    old = packets[2].payload
    packets[2] = Packet(0x7D5C, old[:129] + b"\x64" + old[130:])
    predicted = decode_frame(bytes(4095) + encode_packets(packets))
    registration = {
        "analysis_version": "fine-tempo80-to100-control-preregistration-0.1",
        "registered_before_capture": True,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": acceptance["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_capture_sha256": acceptance["capture_sha256"],
        "baseline_body_sha256": acceptance["body_sha256"],
        "baseline_acceptance_sha256": sha256_file(acceptance_path),
        "candidate": {
            "tag": "0x7d5c",
            "occurrence_index_zero_based": 1,
            "payload_offset_zero_based": 129,
            "baseline_encoded_value": 80,
            "hypothesis": "Fine tempo uses the same direct integer BPM byte; only byte129 changes80 to100",
        },
        "expected_before_display_bpm": 80,
        "requested_after_display_bpm": 100,
        "expected100_body_sha256": hashlib.sha256(predicted.encoded_body).hexdigest(),
        "official_control_reference": {
            "url": "https://teenage.engineering/guides/po-33/en",
            "reviewed_date": "2026-10-09",
            "section": "6, tempo",
            "paraphrase": "Hold BPM and turn knob B for fine tempo; knob A controls swing and is excluded",
        },
        "limits": [
            "Only the physical fine-tempo100 observation is requested; the prediction is not a generated restore",
            "Public tempo editing remains restricted to80/120/140 and the recognized opaque context",
            "Record the actual display value independently if100 cannot be reached; do not infer it from bytes",
            "Other global or sound-parameter changes remain visible; touching knob B is allowed only while BPM is held",
        ],
    }
    controls, fits, _ = comparison_checks(base, predicted, registration, 80, 100)
    assert all(controls.values()) and all(fits.values())
    validation_path = root / "experiments/fine-tempo100-prediction-validation-001.json"
    validate_outputs([validation_path], [acceptance_path, source_path], False)
    directory.mkdir()
    write_bytes(directory / "predicted-native-body.bin", predicted.encoded_body)
    write_bytes(directory / "tempo-registration.json", json_bytes(registration))
    write_bytes(
        validation_path,
        json_bytes(
            {
                "analysis_version": "fine-tempo100-software-prediction-check-0.1",
                "hardware_verified": False,
                "passed": True,
                "checks": {
                    "all_synthetic_core_controls": all(controls.values()),
                    "all_synthetic_single_byte_hypotheses": all(fits.values()),
                },
                "registration_sha256": sha256_file(directory / "tempo-registration.json"),
                "expected100_body_sha256": registration["expected100_body_sha256"],
            }
        ),
    )
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": directory.name,
                "capture_status": "awaiting_physical_fine_tempo100",
                "baseline_id": baseline.name,
                "expected_file": "capture.wav",
                "registration": "tempo-registration.json",
                "planned_actions": [
                    "Keep Pattern1/Sound8/TONE stopped/write off; note initial displayed80 BPM",
                    "Hold BPM continuously while turning knob B to displayed100; stop moving B before releasing BPM; do not move knob A",
                    "Before playback capture a complete stereo backup at established reduced levels with one second trailing silence",
                    "Report actual displayed BPM before/after and leave the fine tempo in place; do not touch either knob further",
                ],
            }
        ),
    )
    print(
        json.dumps(
            {"registered": True, "expected100_body_sha256": registration["expected100_body_sha256"]}
        )
    )


if __name__ == "__main__":
    main()
