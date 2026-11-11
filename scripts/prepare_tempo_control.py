"""Register one BPM-button press without assuming that tempo is serialized."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact


def run(directory):
    root = Path(__file__).resolve().parents[1]
    if directory.exists() or directory.is_symlink() or not directory.parent.is_dir():
        raise ValueError("Fresh output directory with an existing parent required")
    baseline = root / "experiments/event-029-b-delete-imported-unshared-sound7"
    acceptance_path = baseline / "hardware-acceptance-001.json"
    acceptance = json.loads(acceptance_path.read_text())
    source_path = root / acceptance["artifact_path"]
    if (
        not acceptance["hardware_verified"]
        or not all(acceptance["checks"].values())
        or sha256_file(source_path) != acceptance["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != acceptance["capture_sha256"]
    ):
        raise ValueError("Verified unchanged baseline required")
    frame = decode_artifact(load_artifact(source_path))
    globals_ = [(i, p) for i, p in enumerate(frame.packets) if p.tag == 0x7D5C]
    if hashlib.sha256(frame.encoded_body).hexdigest() != acceptance["body_sha256"] or [
        len(p.payload) for _, p in globals_
    ] != [255, 255]:
        raise ValueError("Expected verified baseline and two opaque global records")
    registration = {
        "analysis_version": "single-BPM-button-tempo-control-preregistration-0.1",
        "registered_before_capture": True,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": acceptance["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_capture_sha256": acceptance["capture_sha256"],
        "baseline_body_sha256": acceptance["body_sha256"],
        "baseline_acceptance_sha256": sha256_file(acceptance_path),
        "global_records": [
            {
                "packet_index": i,
                "payload_sha256": hashlib.sha256(p.payload).hexdigest(),
                "payload_hex": p.payload.hex(),
            }
            for i, p in globals_
        ],
        "candidate": {
            "tag": "0x7d5c",
            "occurrence_index_zero_based": 1,
            "payload_offset_zero_based": 129,
            "baseline_encoded_value": globals_[1][1].payload[129],
            "hypothesis": "Second opaque global packet byte129 stores the displayed integer BPM directly; only this byte changes after one BPM preset press",
            "basis": "Before collection, the mostly-zero prefix has byte128=1 and byte129=120; numeric coincidence is a lead, not field identification",
            "baseline_device_display_bpm": None,
        },
        "official_control_reference": {
            "url": "https://teenage.engineering/guides/po-33/en",
            "reviewed_date": "2026-10-09",
            "section": "6, tempo",
            "paraphrase": "Pressing BPM cycles tempo presets 80, 120 and 140; holding BPM with a knob changes swing or fine tempo and is excluded from this control",
        },
        "limits": [
            "Tempo storage and the candidate offset are unverified; no tempo writer is enabled",
            "A valid identical body remains an eligible no-serialized-change outcome",
            "BPM values must come from the user's display observation, not from candidate bytes",
            "Changes elsewhere or multiple changed bytes remain visible and may reject the single-byte hypothesis",
        ],
    }
    directory.mkdir()
    write_bytes(directory / "tempo-registration.json", json_bytes(registration))
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": directory.name,
                "capture_status": "awaiting_single_BPM_button_control",
                "baseline_id": baseline.name,
                "expected_file": "capture.wav",
                "registration": "tempo-registration.json",
                "requested_observations": [
                    "BPM displayed before",
                    "BPM displayed after one short BPM button press",
                ],
                "planned_actions": [
                    "Keep Pattern1/Sound8/TONE stopped/write off and both knobs unchanged",
                    "Note the displayed BPM, tap BPM once without holding or turning a knob, note the new displayed BPM",
                    "Before playback or audition save a complete stereo capture.wav at established reduced levels with one second trailing silence",
                    "Report the displayed BPM before and after with the capture",
                ],
            }
        ),
    )
    return registration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out_dir)
    print(json.dumps({"registered": True, "candidate": result["candidate"]}))


if __name__ == "__main__":
    main()
