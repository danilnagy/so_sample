"""Prepare a source-bound offbeat pattern pair at swing0 and new interior value6."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    frame_report,
    rebuild_labels,
)
from po33_re.formats.patterns import clone_step, pattern_data
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact

SOURCE_BODY = "51b9358a087173aa4ebd4e49eda47e698ba34c7dd077237ccb7d353291b6eea8"
DIRECTORIES = ("edited-swing-timing0-001", "edited-swing-timing6-001")


def candidate_packets(frame, swing):
    """Research only: require exact genuine S18 state; preserve the copied opaque row."""
    if type(swing) is not int or swing not in (0, 6):
        raise ValueError("Only registered research swing targets0 and6 are allowed")
    if hashlib.sha256(frame.encoded_body).hexdigest() != SOURCE_BODY:
        raise ValueError("Exact independently verified S18 native state required")
    packets = list(clone_step(frame, 1, 13, [2]))
    data = packets[2].payload
    packets[2] = Packet(0x7D5C, data[:130] + bytes([swing]) + data[131:])
    return tuple(packets)


def target_checks(base, target, swing):
    before, after = pattern_data(base, 1), pattern_data(target, 1)
    expected = bytearray(before)
    expected[48:96] = before[576:624]
    expected[784:800] = before[960:976]
    globals_before, globals_after = base.packets[2].payload, target.packets[2].payload
    return {
        "exact_source_identity": hashlib.sha256(base.encoded_body).hexdigest() == SOURCE_BODY,
        "target_swing_and_tempo": globals_after[129:131] == bytes([137, swing]),
        "only_swing_global_byte_changed": globals_before[:130] == globals_after[:130]
        and globals_before[131:] == globals_after[131:],
        "pattern1_exact_source13_to_empty2_clone": after == bytes(expected),
        "offbeat_and_reference_same_sound3_key16": after[54:57]
        == after[582:585]
        == bytes.fromhex("0df883")
        and after[786] == after[962] == 0xFF,
        "other15_patterns_exact": all(
            pattern_data(base, slot) == pattern_data(target, slot) for slot in range(2, 17)
        ),
        "all_non_global_non_pattern_packets_exact": tuple(
            p for p in base.packets if p.tag not in (0x7D5C, 0xC498)
        )
        == tuple(p for p in target.packets if p.tag not in (0x7D5C, 0xC498)),
        "first_global_exact": base.packets[1] == target.packets[1],
        "all_packet_layouts_exact": [(p.tag, len(p.payload)) for p in base.packets]
        == [(p.tag, len(p.payload)) for p in target.packets],
        "native_geometry_exact": len(target.packets) == 815 and target.end_byte == 156758,
    }


def run():
    root = Path(__file__).resolve().parents[1]
    outputs = [root / "experiments" / name for name in DIRECTORIES]
    registration_path = root / "experiments/swing-timing-pair-registration-001.json"
    if registration_path.exists() or any(path.exists() or path.is_symlink() for path in outputs):
        raise ValueError("Fresh registration and both output directories required")
    series_path = root / "experiments/swing-range-series-results-001.json"
    series = json.loads(series_path.read_text())
    if not series["series_supported"] or not all(series["return_hypotheses"].values()):
        raise ValueError("Completed independent physical swing range required")
    evidence = []
    for folder, text, value in zip(series["captures"], ("S00", "S09", "S18"), (0, 9, 18)):
        directory = root / "experiments" / folder["experiment_id"]
        observation_path = directory / "hardware-observation-001.json"
        observation = json.loads(observation_path.read_text())
        artifact = root / observation["artifact_path"]
        if (
            not observation["hardware_verified"]
            or not all(observation["checks"].values())
            or observation["display_text"] != text
            or observation["display_numeric_component"] != value
            or sha256_file(artifact) != observation["artifact_sha256"]
            or sha256_file(directory / "capture.wav") != observation["capture_sha256"]
            or observation["series_results_sha256"] != sha256_file(series_path)
        ):
            raise ValueError("Registered physical range evidence differs")
        evidence.append(
            {
                "observation": observation_path.relative_to(root).as_posix(),
                "observation_sha256": sha256_file(observation_path),
                **folder,
            }
        )
    source_path = root / observation["artifact_path"]
    source = load_artifact(source_path)
    source_bytes = source.to_bytes()
    base = decode_artifact(source)
    legs, targets = [], []
    for directory, swing in zip(outputs, (0, 6)):
        edited = rebuild_labels(source, candidate_packets(base, swing))
        edited.metadata["transformations"].append(
            {
                "kind": "research-swing-timing-pair",
                "swing": swing,
                "pattern_clone": {"pattern": 1, "source_step": 13, "target_step": 2},
                "hardware_verified": False,
            }
        )
        target = decode_artifact(edited)
        checks = target_checks(base, target, swing)
        if not all(checks.values()):
            raise ValueError("Swing timing candidate preservation failed")
        waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
        directory.mkdir()
        write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
        write_bytes(directory / "restore.wav", waveform)
        recovered = decode_wav(directory / "restore.wav", 0.02)
        write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
        strict = compare_artifacts(edited, recovered)
        actual = decode_artifact(recovered)
        checks.update(
            strict_phase_roundtrip=strict["passed"],
            entire_body_after_wav_decode=actual.encoded_body == target.encoded_body,
            entire_plain_packets_after_wav_decode=actual.packets == target.packets,
            source_preserved=source.to_bytes() == source_bytes
            and sha256_file(source_path) == observation["artifact_sha256"],
        )
        report = {
            "analysis_version": "research-swing-timing-pair-software-validation-0.1",
            "hardware_verified": False,
            "passed": all(checks.values()),
            "checks": checks,
            "encoding": encoding,
            "strict_phase_roundtrip": strict,
            "source_artifact_sha256": sha256_file(source_path),
            "target_frame": frame_report(target),
            "restore_wav_sha256": sha256_file(directory / "restore.wav"),
            "edited_artifact_sha256": sha256_file(directory / "edited.symbols.npz"),
        }
        write_bytes(directory / "software-validation.json", json_bytes(report))
        if not report["passed"]:
            raise ValueError("Software waveform checks failed; outputs retained")
        legs.append(
            {
                "experiment_id": directory.name,
                "swing_byte": swing,
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "edited_artifact_sha256": report["edited_artifact_sha256"],
                "software_validation_sha256": sha256_file(directory / "software-validation.json"),
                "backup_file": "capture.wav",
                "ordinary_playback_file": "playback.wav",
            }
        )
        targets.append(target)
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_straight_offbeat_control"
                    if swing == 0
                    else "awaiting_verified_straight_control_then_swing6_restore",
                    "hardware_restore": {"status": "not_run"},
                    "registration": "../swing-timing-pair-registration-001.json",
                    "planned_actions": [
                        "For swing6 wait until straight-control capture and playback have been verified",
                        "Restore complete restore.wav with established stereo path and level",
                        "Keep both knobs untouched; select Pattern1/Sound8/TONE, stopped and write off",
                        "Before pattern playback record complete capture.wav at established backup levels and one second trailing silence",
                        "In a separate ordinary-audio recording play Pattern1 for8 to10 seconds; save playback.wav then stop",
                        "Report restore success and audible added high tone after first beat; do not read swing by moving A",
                    ],
                }
            ),
        )
    a, b = targets
    pair_checks = {
        "identical_all_pattern_bytes": all(
            pattern_data(a, s) == pattern_data(b, s) for s in range(1, 17)
        ),
        "only_one_plain_payload_byte_differs": [
            (i, j)
            for i, (p, q) in enumerate(zip(a.packets, b.packets))
            for j, (x, y) in enumerate(zip(p.payload, q.payload))
            if x != y
        ]
        == [(2, 130)],
    }
    if not all(pair_checks.values()):
        raise ValueError("Pair must isolate swing with identical offbeat pattern")
    registration = {
        "analysis_version": "swing-timing-pair-preregistration-0.1",
        "registered_before_all_captures": True,
        "hardware_verified": False,
        "source_artifact": source_path.relative_to(root).as_posix(),
        "source_artifact_sha256": sha256_file(source_path),
        "source_body_sha256": SOURCE_BODY,
        "physical_series_sha256": sha256_file(series_path),
        "independent_display_evidence": evidence,
        "expected_capture_sequence": legs,
        "pair_checks": pair_checks,
        "timing_hypotheses": {
            "identical_sound3_key16_events": "Pattern1 steps2 and13; same opaque primary and auxiliary values and same sample window",
            "zero_swing_reference": "Successive high-note onset gaps alternate11 and5 sixteenth steps; entire cycle16 steps",
            "six_swing_probe": "Compared with swing0, same-parity-to-offbeat gap increases and opposite gap decreases; entire loop period remains constant",
            "nominal_loop_seconds": 16 * 60 / (137 * 4),
            "measure_without_assumed_units": "Use repeated onset pairs and common high-tone component; report measured interval differences, never fit byte to percent or clock units",
            "insufficient_audio": "If high-note onsets cannot be resolved consistently across at least3 full cycles, report timing unevaluated and request clearer or longer playback",
        },
        "limits": [
            "Target6 is a new interior numeric hypothesis; no public swing writer enabled",
            "Software reports never become hardware verified; raw recaptures and ordinary playback are separate evidence",
            "Swing display is not read by turning A because that would change the restored state",
            "First verify straight control before asking for the second restore; timing units remain unknown",
        ],
    }
    write_bytes(registration_path, json_bytes(registration))
    print(json.dumps({"passed": True, "pair_checks": pair_checks, "targets": legs}))


if __name__ == "__main__":
    run()
