"""Register a first swing maximum control without assuming its units or encoding."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.globals import calibrated_tempo
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-037-b-swing-maximum"
    if directory.exists() or directory.is_symlink():
        raise ValueError("Fresh capture directory required")
    baseline = root / "experiments/edited-fine-tempo137-001"
    acceptance_path = baseline / "hardware-acceptance-001.json"
    acceptance = json.loads(acceptance_path.read_text())
    source_path = root / acceptance["artifact_path"]
    if (
        not acceptance["hardware_verified"]
        or not acceptance["fine_tempo_writer_verified"]
        or not all(acceptance["checks"].values())
        or sha256_file(source_path) != acceptance["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != acceptance["capture_sha256"]
    ):
        raise ValueError("Unchanged accepted generated137 source required")
    frame = decode_artifact(load_artifact(source_path))
    if (
        calibrated_tempo(frame) != 137
        or hashlib.sha256(frame.encoded_body).hexdigest() != acceptance["body_sha256"]
    ):
        raise ValueError("Expected accepted137 baseline")
    second = frame.packets[2].payload
    registration = {
        "analysis_version": "first-swing-clockwise-maximum-control-preregistration-0.1",
        "registered_before_capture": True,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": acceptance["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_capture_sha256": acceptance["capture_sha256"],
        "baseline_body_sha256": acceptance["body_sha256"],
        "baseline_acceptance_sha256": sha256_file(acceptance_path),
        "expected_tempo_bpm": 137,
        "global_records": [
            {
                "packet_index": i,
                "payload_hex": frame.packets[i].payload.hex(),
                "payload_sha256": hashlib.sha256(frame.packets[i].payload).hexdigest(),
            }
            for i in (1, 2)
        ],
        "candidate": {
            "tag": "0x7d5c",
            "occurrence_index_zero_based": 1,
            "payload_offset_zero_based": 130,
            "baseline_encoded_value": second[130],
            "hypothesis": "Only the byte immediately after tempo changes when setting maximum swing",
            "basis": "Adjacent mostly-zero global bytes are a preregistered location lead, not a confirmed swing field",
            "expected_after_encoded_value": None,
            "baseline_display_value": None,
        },
        "official_reference": {
            "url": "https://teenage.engineering/guides/po-33/en",
            "reviewed_date": "2026-10-09",
            "section": "6, swing",
            "paraphrase": "Hold BPM and turn knob A to adjust swing; knob B adjusts tempo and is excluded",
        },
        "limits": [
            "Maximum swing is an endpoint action, not an assumed numeric percentage or byte value",
            "Report any display label/value independently, or state that no numeric value is shown",
            "An unchanged capture remains an eligible already-at-maximum or no-serialized-change outcome",
            "All raw differences are reported without fitting a new location; no swing writer is enabled",
        ],
    }
    directory.mkdir()
    write_bytes(directory / "swing-registration.json", json_bytes(registration))
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": directory.name,
                "capture_status": "awaiting_physical_swing_maximum",
                "baseline_id": baseline.name,
                "expected_file": "capture.wav",
                "registration": "swing-registration.json",
                "planned_actions": [
                    "Keep Pattern1/Sound8/TONE stopped/write off; do not move knob B",
                    "Hold BPM continuously while turning only knob A fully clockwise; note any swing display value or label",
                    "Stop moving A before releasing BPM, then leave both knobs unchanged; read tempo without pressing BPM and report expected137",
                    "Before playback record complete stereo capture.wav at established reduced levels with one second trailing silence",
                    "Report the swing display text or no numeric display, and confirm tempo unchanged",
                ],
            }
        ),
    )
    print(
        json.dumps(
            {
                "registered": True,
                "candidate_offset": 130,
                "baseline_encoded_value": second[130],
                "expected_tempo_bpm": 137,
            }
        )
    )


if __name__ == "__main__":
    main()
