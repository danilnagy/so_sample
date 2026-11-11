"""Prepare a generated unobserved fine tempo after physical endpoint and return controls."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    encode_packets,
    frame_report,
    rebuild_labels,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo_control import comparison_checks

ORIGINAL100_BODY = "d01d2cdd2f9cd85aca19e17ebc7967327aba647926faf91dcb2db0fe42de2633"


def fine137_candidate_packets(frame):
    """Research-only100-to137 edit of the complete independently known source state."""
    if hashlib.sha256(frame.encoded_body).hexdigest() != ORIGINAL100_BODY:
        raise ValueError("Exact independently verified fine100 native state required")
    if (
        [i for i, p in enumerate(frame.packets) if p.tag == 0x7D5C] != [1, 2]
        or len(frame.packets[2].payload) != 255
        or frame.packets[2].payload[129] != 100
    ):
        raise ValueError("Observed fine100 global record required")
    packets = list(frame.packets)
    data = packets[2].payload
    packets[2] = Packet(0x7D5C, data[:129] + b"\x89" + data[130:])
    return tuple(packets)


def run(directory):
    root = Path(__file__).resolve().parents[1]
    if directory.exists() or directory.is_symlink() or not directory.parent.is_dir():
        raise ValueError("Fresh output directory with existing parent required")
    baseline = root / "experiments/event-036-a-return-fine-tempo-100"
    observation_path = baseline / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    series_path = root / "experiments/fine-tempo-range-series-results-001.json"
    series = json.loads(series_path.read_text())
    if (
        not series["control_passed"]
        or not series["series_supported"]
        or not all(series["return_hypotheses"].values())
        or not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or observation["display_bpm"] != 100
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Verified fine endpoints and exact returned100 source required")
    source = load_artifact(source_path)
    unchanged = source.to_bytes()
    base = decode_artifact(source)
    bounds = []
    boundary_checks = {}
    for name, bpm in (("event-034-b-fine-tempo-60", 60), ("event-035-c-fine-tempo-240", 240)):
        folder = root / "experiments" / name
        result_path = folder / "hardware-observation-001.json"
        result = json.loads(result_path.read_text())
        path = root / result["artifact_path"]
        if (
            not result["hardware_verified"]
            or not all(result["checks"].values())
            or result["display_bpm"] != bpm
            or sha256_file(path) != result["artifact_sha256"]
            or sha256_file(folder / "capture.wav") != result["capture_sha256"]
        ):
            raise ValueError("Independent endpoint evidence differs")
        actual = decode_artifact(load_artifact(path))
        predicted = list(base.packets)
        old = predicted[2].payload
        predicted[2] = Packet(0x7D5C, old[:129] + bytes([bpm]) + old[130:])
        boundary_checks[f"reproduces_entire_genuine{bpm}_body"] = (
            encode_packets(predicted) == actual.encoded_body
        )
        bounds.append(
            {
                "bpm": bpm,
                "artifact": path.relative_to(root).as_posix(),
                "artifact_sha256": result["artifact_sha256"],
                "body_sha256": result["body_sha256"],
                "observation_sha256": sha256_file(result_path),
            }
        )
    edited = rebuild_labels(source, fine137_candidate_packets(base))
    edited.metadata["transformations"].append(
        {"kind": "generated-unobserved-fine-tempo100-to137-probe", "hardware_verified": False}
    )
    target = decode_artifact(edited)
    registration = {
        "analysis_version": "first-generated-fine137-preregistration-0.1",
        "registered_before_capture": True,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": observation["artifact_sha256"],
        "baseline_capture": (baseline / "capture.wav").relative_to(root).as_posix(),
        "baseline_capture_sha256": observation["capture_sha256"],
        "baseline_body_sha256": observation["body_sha256"],
        "baseline_observation_sha256": sha256_file(observation_path),
        "physical_range_series_results_sha256": sha256_file(series_path),
        "independent_endpoint_evidence": bounds,
        "candidate": {
            "tag": "0x7d5c",
            "occurrence_index_zero_based": 1,
            "payload_offset_zero_based": 129,
            "baseline_encoded_value": 100,
        },
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_display_bpm": 137,
        "expected_packet_count": 815,
        "expected_frame_end_byte": 156758,
        "limits": [
            "137 is not a previously captured physical target; this is an independent generated fine-tempo probe",
            "Public tempo editing remains the three presets until suitable fine-restore evidence",
            "Software reports remain hardware-unverified; independent display and complete recapture are required",
            "Only the fixed byte changes; unknown global or sound parameters are preserved",
        ],
    }
    controls, fits, _ = comparison_checks(base, target, registration, 100, 137)
    checks = dict(
        boundary_checks,
        all_target_core_controls=all(controls.values()),
        all_target_fixed_byte_hypotheses=all(fits.values()),
        source_artifact_preserved=source.to_bytes() == unchanged,
    )
    if not all(checks.values()):
        raise ValueError("Fine137 source, independent bounds or preservation checks failed")
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    directory.mkdir()
    write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
    write_bytes(directory / "restore.wav", waveform)
    recovered = decode_wav(directory / "restore.wav", 0.02)
    write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
    comparison = compare_artifacts(edited, recovered)
    decoded = decode_artifact(recovered)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        entire_target_body_after_wav_decode=decoded.encoded_body == target.encoded_body,
        entire_target_plain_packets_after_wav_decode=decoded.packets == target.packets,
        source_file_preserved=sha256_file(source_path) == observation["artifact_sha256"],
    )
    report = dict(registration)
    report.update(
        analysis_version="first-generated-fine137-software-validation-0.1",
        hardware_verified=False,
        passed=all(checks.values()),
        checks=checks,
        encoding=encoding,
        strict_phase_roundtrip=comparison,
        target_frame=frame_report(target),
        restore_wav_sha256=sha256_file(directory / "restore.wav"),
        edited_artifact_sha256=sha256_file(directory / "edited.symbols.npz"),
    )
    write_bytes(directory / "software-validation.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Fine137 waveform checks failed; outputs retained")
    registration.update(
        restore_wav_sha256=report["restore_wav_sha256"],
        edited_artifact_sha256=report["edited_artifact_sha256"],
        software_validation_sha256=sha256_file(directory / "software-validation.json"),
    )
    write_bytes(directory / "restore-registration.json", json_bytes(registration))
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": directory.name,
                "capture_status": "awaiting_generated_fine_tempo137_restore",
                "expected_file": "capture.wav",
                "restore_file": "restore.wav",
                "registration": "restore-registration.json",
                "hardware_restore": {"status": "not_run", "observations": []},
                "planned_actions": [
                    "Restore complete restore.wav through the established stereo playback path and level",
                    "Return to Pattern1/Sound8/TONE stopped/write off; keep both knobs unchanged",
                    "Read displayed BPM without pressing BPM; report actual value, expected137",
                    "Before playback save complete stereo capture.wav at established reduced levels with one second trailing silence",
                    "After saving confirm Pattern1 retains the same phrase at the new tempo and samples sound unchanged; stop and return to Sound8/TONE",
                ],
            }
        ),
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.out_dir)
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "expected_body_sha256": report["expected_body_sha256"],
                "restore_wav_sha256": report["restore_wav_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
