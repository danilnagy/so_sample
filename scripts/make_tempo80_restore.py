"""Prepare the first generated tempo edit against the independently observed80 body."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import Packet, decode_artifact, frame_report, rebuild_labels
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo_control import comparison_checks

ORIGINAL120_BODY = "12acce04d44039abcda973f1e6590f47ac798610e40f4ef440f8322a7b3bebd0"
OBSERVED80_BODY = "2a1a594b027dcd228f20e2b72961e995b27a3c8378643d74ad03a323ce3c17ce"


def tempo80_candidate_packets(frame):
    """Research-only edit of the exact known120 native state, not an arbitrary writer."""
    if hashlib.sha256(frame.encoded_body).hexdigest() != ORIGINAL120_BODY:
        raise ValueError("Exact independently verified original120 native state required")
    indices = [i for i, p in enumerate(frame.packets) if p.tag == 0x7D5C]
    if len(indices) != 2 or any(len(frame.packets[i].payload) != 255 for i in indices):
        raise ValueError("Observed two-global-record geometry required")
    index = indices[1]
    data = frame.packets[index].payload
    if data[129] != 120:
        raise ValueError("Observed120 candidate byte required")
    packets = list(frame.packets)
    packets[index] = Packet(0x7D5C, data[:129] + b"\x50" + data[130:])
    return tuple(packets)


def run(directory):
    root = Path(__file__).resolve().parents[1]
    if directory.exists() or directory.is_symlink() or not directory.parent.is_dir():
        raise ValueError("Fresh output directory with existing parent required")
    source_dir = root / "experiments/event-032-a-return-tempo-120"
    genuine_dir = root / "experiments/event-031-b-tempo-80"
    source_observation_path = source_dir / "hardware-observation-001.json"
    genuine_observation_path = genuine_dir / "hardware-observation-001.json"
    source_observation, genuine_observation = [
        json.loads(path.read_text()) for path in (source_observation_path, genuine_observation_path)
    ]
    source_path, genuine_path = [
        root / observation["artifact_path"]
        for observation in (source_observation, genuine_observation)
    ]
    for observation, path, folder in (
        (source_observation, source_path, source_dir),
        (genuine_observation, genuine_path, genuine_dir),
    ):
        if (
            not observation["hardware_verified"]
            or not all(observation["checks"].values())
            or sha256_file(path) != observation["artifact_sha256"]
            or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
        ):
            raise ValueError("Matching observed120 return and genuine80 capture required")
    source = load_artifact(source_path)
    before_bytes = source.to_bytes()
    original = decode_artifact(source)
    genuine = decode_artifact(load_artifact(genuine_path))
    edited = rebuild_labels(source, tempo80_candidate_packets(original))
    edited.metadata["transformations"].append(
        {"kind": "first-generated-tempo120-to80-probe", "hardware_verified": False}
    )
    target = decode_artifact(edited)
    registration = {
        "analysis_version": "first-generated-tempo80-restore-preregistration-0.1",
        "registered_before_capture": True,
        "baseline_artifact": source_path.relative_to(root).as_posix(),
        "baseline_artifact_sha256": source_observation["artifact_sha256"],
        "baseline_capture": (source_dir / "capture.wav").relative_to(root).as_posix(),
        "baseline_capture_sha256": source_observation["capture_sha256"],
        "baseline_body_sha256": source_observation["body_sha256"],
        "baseline_observation_sha256": sha256_file(source_observation_path),
        "genuine80_artifact": genuine_path.relative_to(root).as_posix(),
        "genuine80_artifact_sha256": genuine_observation["artifact_sha256"],
        "genuine80_observation_sha256": sha256_file(genuine_observation_path),
        "expected_body_sha256": OBSERVED80_BODY,
        "expected_packet_count": 815,
        "expected_frame_end_byte": 156758,
        "candidate": {
            "tag": "0x7d5c",
            "occurrence_index_zero_based": 1,
            "payload_offset_zero_based": 129,
            "baseline_encoded_value": 120,
        },
        "expected_display_bpm": 80,
        "limits": [
            "Only this exact independently known120 state to the observed80 target is tested",
            "Generated software reports remain unverified by hardware until separate restore/recapture evidence",
            "No public tempo writer or arbitrary BPM range is enabled",
        ],
    }
    controls, fits, _ = comparison_checks(original, target, registration, 120, 80)
    checks = {
        "all_candidate_core_controls": all(controls.values()),
        "all_candidate_tempo_hypotheses": all(fits.values()),
        "target_equals_complete_genuine80_body": target.encoded_body == genuine.encoded_body
        and hashlib.sha256(genuine.encoded_body).hexdigest() == OBSERVED80_BODY,
        "target_equals_complete_genuine80_plain_packets": target.packets == genuine.packets,
        "source_artifact_preserved": source.to_bytes() == before_bytes,
    }
    if not all(checks.values()):
        raise ValueError("Tempo candidate differs from the independently genuine80 state")
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    directory.mkdir()
    write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
    write_bytes(directory / "restore.wav", waveform)
    recovered = decode_wav(directory / "restore.wav", 0.02)
    write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
    comparison = compare_artifacts(edited, recovered)
    redecoded = decode_artifact(recovered)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        whole_target_body_after_wav_decode=redecoded.encoded_body == target.encoded_body,
        whole_target_plain_packets_after_wav_decode=redecoded.packets == target.packets,
        source_file_preserved=sha256_file(source_path) == source_observation["artifact_sha256"],
    )
    report = dict(registration)
    report.update(
        analysis_version="first-generated-tempo80-software-validation-0.1",
        hardware_verified=False,
        checks=checks,
        passed=all(checks.values()),
        encoding=encoding,
        strict_phase_roundtrip=comparison,
        target_frame=frame_report(target),
        restore_wav_sha256=sha256_file(directory / "restore.wav"),
        edited_artifact_sha256=sha256_file(directory / "edited.symbols.npz"),
    )
    write_bytes(directory / "software-validation.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Tempo waveform checks failed; outputs retained")
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
                "capture_status": "awaiting_first_generated_tempo80_restore",
                "expected_file": "capture.wav",
                "restore_file": "restore.wav",
                "registration": "restore-registration.json",
                "hardware_restore": {"status": "not_run", "observations": []},
                "planned_actions": [
                    "Restore the complete restore.wav at the established stereo playback level",
                    "Return to Pattern1/Sound8/TONE stopped/write off; keep both knobs unchanged",
                    "Read and report the displayed BPM without pressing BPM; expected80",
                    "Before audition/playback record a complete stereo capture.wav at established reduced levels with one second trailing silence",
                    "After saving confirm Pattern1 retains the phrase at the slower80 BPM tempo and samples sound unchanged; return to Sound8/TONE",
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
