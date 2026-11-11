"""Register fixed footer7 then FF restores with global7 and every other byte preserved."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, rebuild_labels
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact

UP_BODY = "1147b3d4952aa4ade735b011047bcf22a469855bc3e1fff9c6f6cd4c462ca495"
DOWN_BODY = "01cb7130546dd862c8b9ef290785dd9e6c3094e64e6b9279dae4730edea7cd68"
CLEAR_BODY = "3d3762e28817a2bccf83986539c889d1e74e70139b2313affcc3d56cc1bb370b"
REGISTRATION = "pattern1-generated-FX7-clear-global7-registration-001.json"
LEGS = {
    "down": {
        "experiment_id": "edited-pattern1-FX7-global7-down-001",
        "source_body": UP_BODY,
        "target_body": DOWN_BODY,
        "footer": 0x77,
    },
    "clear": {
        "experiment_id": "edited-pattern1-FX15-global7-clear-001",
        "source_body": DOWN_BODY,
        "target_body": CLEAR_BODY,
        "footer": 0xFF,
    },
}


def fixed_return_packets(frame, leg):
    if leg not in LEGS:
        raise ValueError("Only fixed down/clear research legs allowed")
    spec = LEGS[leg]
    if hashlib.sha256(frame.encoded_body).hexdigest() != spec["source_body"]:
        raise ValueError("Exact fixed-leg source body required")
    data = bytearray(pattern_data(frame, 1))
    data[1024:] = bytes([spec["footer"]]) * 8
    return _replace_pattern_data(frame, 1, bytes(data))


def return_checks(base, actual, leg):
    if leg not in LEGS:
        raise ValueError("Only fixed down/clear research legs allowed")
    spec = LEGS[leg]
    data = bytearray(pattern_data(actual, 1))
    footer_correct = data[1024:] == bytes([spec["footer"]]) * 8
    data[1024:] = pattern_data(base, 1)[1024:]
    reverted = _replace_pattern_data(actual, 1, bytes(data))
    return {
        "source_is_exact_fixed_leg_body": hashlib.sha256(base.encoded_body).hexdigest()
        == spec["source_body"],
        "source_and_actual_native_valid": all(
            len(frame.packets) == 815
            and frame.end_byte == 156758
            and encode_packets(frame.packets) == frame.encoded_body
            for frame in (base, actual)
        ),
        "all16_footer_nibbles_match_fixed_leg": footer_correct,
        "only_eight_Pattern1_footer_bytes_changed": tuple(reverted) == base.packets,
        "global131_stays7": base.packets[2].payload[131] == actual.packets[2].payload[131] == 7,
        "entire_fixed_leg_target_body_exact": hashlib.sha256(actual.encoded_body).hexdigest()
        == spec["target_body"],
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    folders = [root / "experiments" / spec["experiment_id"] for spec in LEGS.values()]
    if any(path.exists() or path.is_symlink() for path in [registration_path, *folders]):
        raise ValueError("Fresh fixed-return registration and folders required")
    source_folder = root / "experiments/edited-pattern1-FX6-global7-up-001"
    observation_path = source_folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(source_folder / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Accepted generated footer6/global7 source required")
    baseline_folder = root / "experiments/event-070-b-pattern1-plain-playback"
    baseline_observation_path = baseline_folder / "hardware-observation-001.json"
    baseline = json.loads(baseline_observation_path.read_text())
    if (
        not baseline["hardware_verified"]
        or not all(baseline["checks"].values())
        or sha256_file(root / baseline["artifact_path"]) != baseline["artifact_sha256"]
        or sha256_file(baseline_folder / "capture.wav") != baseline["capture_sha256"]
    ):
        raise ValueError("Independent exact clear baseline required")
    original_clear = decode_artifact(load_artifact(root / baseline["artifact_path"]))
    edited_source = load_artifact(source_path)
    prepared = []
    for (leg, spec), folder in zip(LEGS.items(), folders):
        source_before = edited_source.to_bytes()
        base = decode_artifact(edited_source)
        edited = rebuild_labels(edited_source, fixed_return_packets(base, leg))
        edited.metadata["transformations"].append(
            {
                "kind": "research-fixed-Pattern1-footer-" + leg + "-global7-preserved",
                "hardware_verified": False,
            }
        )
        target = decode_artifact(edited)
        checks = return_checks(base, target, leg)
        if not all(checks.values()):
            raise ValueError("Fixed-return native preservation failed")
        waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
        folder.mkdir()
        write_bytes(folder / "edited.symbols.npz", edited.to_bytes())
        write_bytes(folder / "restore.wav", waveform)
        recovered = decode_wav(folder / "restore.wav", 0.02)
        write_bytes(folder / "redecoded.symbols.npz", recovered.to_bytes())
        actual = decode_artifact(recovered)
        comparison = compare_artifacts(edited, recovered)
        checks.update(
            strict_phase_roundtrip=comparison["passed"],
            entire_target_after_waveform_decode=actual.packets == target.packets
            and actual.encoded_body == target.encoded_body,
            source_unchanged=edited_source.to_bytes() == source_before,
        )
        if leg == "clear":
            checks["entire_independent_clear_baseline_return"] = (
                target.packets == original_clear.packets
                and target.encoded_body == original_clear.encoded_body
            )
        validation_path = folder / "software-validation.json"
        write_bytes(
            validation_path,
            json_bytes(
                {
                    "analysis_version": "fixed-return-footer-global7-waveform-validation-0.1",
                    "hardware_verified": False,
                    "passed": all(checks.values()),
                    "checks": checks,
                    "encoding": encoding,
                    "target_frame": frame_report(target),
                    "strict_phase_roundtrip": comparison,
                }
            ),
        )
        if not all(checks.values()):
            raise ValueError("Fixed-return waveform failed; outputs retained")
        actions = [
            "Restore restore.wav using established stereo settings, after the preceding leg if this is clear",
            "Playback stopped, write off, knobs untouched: record complete capture.wav BEFORE listening playback",
            "With write off, play Pattern1 briefly and report whether it sounds octave-lower for down, or normal for clear; stop afterward",
            "Do not press FX, enable write, or move knobs; use established reduced capture level with one second trailing silence",
        ]
        write_bytes(
            folder / "experiment.json",
            json_bytes(
                {
                    "experiment_id": folder.name,
                    "capture_status": "awaiting_restore_and_preplayback_capture",
                    "restore_file": "restore.wav",
                    "registration": "../" + REGISTRATION,
                    "leg": leg,
                    "hardware_restore": {"status": "not_run"},
                    "planned_actions": actions,
                }
            ),
        )
        write_bytes(
            folder / "instructions.md",
            (
                "# Fixed "
                + leg
                + " restore\n\n"
                + "\n".join(f"{i}. {action}" for i, action in enumerate(actions, 1))
                + "\n"
            ).encode(),
        )
        prepared.append(
            dict(
                spec,
                leg=leg,
                edited_artifact_sha256=sha256_file(folder / "edited.symbols.npz"),
                restore_wav_sha256=sha256_file(folder / "restore.wav"),
                software_validation_sha256=sha256_file(validation_path),
            )
        )
        edited_source = edited
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "generated-footer7-and-FF-global7-return-preregistration-0.1",
                "hardware_verified": False,
                "registered_before_both_physical_recaptures": True,
                "source_artifact": observation["artifact_path"],
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (source_folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_observation": observation_path.relative_to(root).as_posix(),
                "source_observation_sha256": sha256_file(observation_path),
                "independent_clear_artifact": baseline["artifact_path"],
                "independent_clear_artifact_sha256": baseline["artifact_sha256"],
                "independent_clear_capture": (baseline_folder / "capture.wav")
                .relative_to(root)
                .as_posix(),
                "independent_clear_capture_sha256": baseline["capture_sha256"],
                "independent_clear_observation": baseline_observation_path.relative_to(
                    root
                ).as_posix(),
                "independent_clear_observation_sha256": sha256_file(baseline_observation_path),
                "expected_capture_sequence": prepared,
                "hypotheses": [
                    "Footer7 alone produces audible octave-down while global131 remains7",
                    "FooterF restores normal playback and the entire independent clear body including global131",
                ],
                "limits": [
                    "Fixed exact-source pair only; no public FX writer, nibble order or complete enum",
                    "Down native target must pass before adjudicating clear; pair may be recorded and uploaded in order together",
                    "Native reception and listening are separate; no measured octave ratio or direction inferred from bytes",
                    "Each physical backup must precede its listening playback; all other bytes including global131 are fixed",
                    "Any failed target or listening hypothesis remains retained; do not widen masks or rewrite prior evidence",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "restore_folders": [folder.name for folder in folders]}))


if __name__ == "__main__":
    main()
