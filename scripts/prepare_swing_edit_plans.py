"""Replay accepted timing WAVs with public plans and prepare a joint tempo100/swing9 edit."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import calibrated_swing, calibrated_tempo
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact


def plan_for(path, operations):
    frame = decode_artifact(load_artifact(path))
    return {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(path),
        "source_body_sha256": hashlib.sha256(frame.encoded_body).hexdigest(),
        "operations": operations,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-swing-timing6-001"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not observation["swing_writer_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Accepted generated swing6 evidence required")
    pair = json.loads((root / "experiments/swing-timing-pair-registration-001.json").read_text())
    replay_source = root / pair["source_artifact"]
    if sha256_file(replay_source) != pair["source_artifact_sha256"]:
        raise ValueError("Original source for accepted timing pair differs")
    records = []
    for value, leg in zip((0, 6), pair["expected_capture_sequence"]):
        plan_directory = root / f"experiments/replay-swing{value}-plan-001"
        output = root / f"experiments/compiled-swing{value}-plan-001"
        if plan_directory.exists() or output.exists():
            raise ValueError("Fresh replay plan and output required")
        plan_directory.mkdir()
        plan_path = plan_directory / "plan.json"
        write_bytes(
            plan_path,
            json_bytes(
                plan_for(
                    replay_source,
                    [
                        {
                            "operation": "clone_step",
                            "pattern": 1,
                            "source_step": 13,
                            "target_steps": [2],
                        },
                        {"operation": "set_swing", "value": value},
                    ],
                )
            ),
        )
        report = compile_edit_plan(replay_source, plan_path, output)
        accepted = root / "experiments" / leg["experiment_id"]
        checks = {
            "compile_checks_pass": report["passed"] and all(report["checks"].values()),
            "accepted_wav_replayed_byte_for_byte": (output / "restore.wav").read_bytes()
            == (accepted / "restore.wav").read_bytes(),
            "registered_complete_body_replayed": report["target_body_sha256"]
            == leg["expected_body_sha256"],
            "compiler_remains_hardware_unverified": report["hardware_verified"] is False,
        }
        if not all(checks.values()):
            raise ValueError("Public swing replay failed; outputs retained")
        records.append(
            {
                "swing": value,
                "plan": plan_path.relative_to(root).as_posix(),
                "plan_sha256": sha256_file(plan_path),
                "compile_report_sha256": sha256_file(output / "compile-report.json"),
                "checks": checks,
            }
        )
    plan_directory = root / "experiments/joint-tempo100-swing9-plan-001"
    output = root / "experiments/edited-joint-tempo100-swing9-001"
    if plan_directory.exists() or output.exists():
        raise ValueError("Fresh joint plan and output required")
    base = decode_artifact(load_artifact(source_path))
    if (calibrated_tempo(base), calibrated_swing(base)) != (137, 6):
        raise ValueError("Expected verified current137/swing6 state")
    plan_directory.mkdir()
    plan_path = plan_directory / "plan.json"
    write_bytes(
        plan_path,
        json_bytes(
            plan_for(
                source_path,
                [
                    {"operation": "set_tempo", "bpm": 100},
                    {"operation": "set_swing", "value": 9},
                ],
            )
        ),
    )
    report = compile_edit_plan(source_path, plan_path, output)
    target = decode_artifact(load_artifact(output / "edited.symbols.npz"))
    differences = [
        (i, j)
        for i, (p, q) in enumerate(zip(base.packets, target.packets))
        for j, (a, b) in enumerate(zip(p.payload, q.payload))
        if a != b
    ]
    checks = {
        "only_two_calibrated_global_bytes_changed": differences == [(2, 129), (2, 130)],
        "target_tempo100_and_swing9": (calibrated_tempo(target), calibrated_swing(target))
        == (100, 9),
        "all_other_plain_packets_exact": base.packets[:2] == target.packets[:2]
        and base.packets[3:] == target.packets[3:],
        "native_geometry_exact": len(target.packets) == 815 and target.end_byte == 156758,
        "waveform_compile_checks_pass": report["passed"] and all(report["checks"].values()),
        "source_file_unchanged": sha256_file(source_path) == observation["artifact_sha256"],
    }
    if not all(checks.values()):
        raise ValueError("Joint edit preservation failed; outputs retained")
    registration = {
        "analysis_version": "joint-tempo100-swing9-preregistration-0.1",
        "registered_before_capture": True,
        "hardware_verified": False,
        "source_artifact": source_path.relative_to(root).as_posix(),
        "source_artifact_sha256": observation["artifact_sha256"],
        "source_capture": (folder / "capture.wav").relative_to(root).as_posix(),
        "source_capture_sha256": observation["capture_sha256"],
        "source_observation_sha256": sha256_file(observation_path),
        "source_body_sha256": observation["body_sha256"],
        "expected_body_sha256": report["target_body_sha256"],
        "expected_tempo_bpm": 100,
        "expected_swing_byte": 9,
        "expected_packet_count": 815,
        "expected_frame_end_byte": 156758,
        "restore_wav_sha256": report["restore_wav_sha256"],
        "edited_artifact_sha256": sha256_file(output / "edited.symbols.npz"),
        "compile_report_sha256": sha256_file(output / "compile-report.json"),
        "plan_sha256": sha256_file(plan_path),
        "software_checks": checks,
        "limits": [
            "This new joint setting needs physical restore and exact recapture",
            "Swing display is not read by turning a knob; independently confirm ordinary BPM display100",
            "No percent/clock timing units or hardware test of every interior value claimed",
        ],
    }
    write_bytes(output / "joint-global-registration.json", json_bytes(registration))
    write_bytes(
        output / "experiment.json",
        json_bytes(
            {
                "experiment_id": output.name,
                "capture_status": "awaiting_joint_tempo100_swing9_restore",
                "expected_file": "capture.wav",
                "restore_file": "restore.wav",
                "registration": "joint-global-registration.json",
                "hardware_restore": {"status": "not_run"},
                "planned_actions": [
                    "Restore complete restore.wav using established stereo playback path and level",
                    "Keep both knobs untouched; select Pattern1/Sound8/TONE stopped and write off",
                    "Read ordinary BPM display without pressing BPM or moving knobs and report actual value; expected100",
                    "Before playing Pattern1 record complete backup capture.wav at established reduced levels with one second trailing silence",
                    "After saving briefly play Pattern1 to confirm same notes and slower swung rhythm; stop and return to Sound8/TONE",
                ],
            }
        ),
    )
    write_bytes(
        root / "experiments/swing-public-plan-workflow-validation-001.json",
        json_bytes(
            {
                "analysis_version": "accepted-swing-public-replay-and-joint-edit-software-validation-0.1",
                "hardware_verified": False,
                "passed": True,
                "replays": records,
                "joint_checks": checks,
                "joint_registration_sha256": sha256_file(output / "joint-global-registration.json"),
            }
        ),
    )
    print(
        json.dumps(
            {
                "passed": True,
                "accepted_wav_replays": 2,
                "joint_checks": checks,
                "joint_body_sha256": report["target_body_sha256"],
                "joint_restore_sha256": report["restore_wav_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
