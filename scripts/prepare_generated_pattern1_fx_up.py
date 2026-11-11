"""Generate only uniform footer6 from the exact accepted clear body; preserve global131."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import (
    decode_artifact,
    encode_packets,
    frame_report,
    rebuild_labels,
)
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact

SOURCE_BODY = "3d3762e28817a2bccf83986539c889d1e74e70139b2313affcc3d56cc1bb370b"
DIRECTORY = "edited-pattern1-FX6-global7-up-001"
REGISTRATION = "pattern1-generated-FX6-global7-up-registration-001.json"


def fixed_up_packets(frame, value=6):
    if hashlib.sha256(frame.encoded_body).hexdigest() != SOURCE_BODY:
        raise ValueError("Exact accepted FF/global7 clear source required")
    if type(value) is not int or value != 6:
        raise ValueError("Only fixed research footer6 allowed")
    data = bytearray(pattern_data(frame, 1))
    data[1024:] = bytes([0x66]) * 8
    return _replace_pattern_data(frame, 1, bytes(data))


def footer_only_checks(base, actual):
    data = bytearray(pattern_data(actual, 1))
    footer_correct = data[1024:] == bytes([0x66]) * 8
    data[1024:] = pattern_data(base, 1)[1024:]
    reverted = _replace_pattern_data(actual, 1, bytes(data))
    return {
        "source_is_exact_accepted_clear_body": hashlib.sha256(base.encoded_body).hexdigest()
        == SOURCE_BODY,
        "source_and_actual_native_valid": all(
            len(frame.packets) == 815
            and frame.end_byte == 156758
            and encode_packets(frame.packets) == frame.encoded_body
            for frame in (base, actual)
        ),
        "all16_footer_nibbles_are6": footer_correct,
        "only_eight_Pattern1_footer_bytes_changed": tuple(reverted) == base.packets
        and pattern_data(base, 1)[1024:] == bytes([0xFF]) * 8,
        "global131_stays7": base.packets[2].payload[131] == actual.packets[2].payload[131] == 7,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if any(path.exists() or path.is_symlink() for path in (folder, registration_path)):
        raise ValueError("Fresh generated FX folder and registration required")
    source_folder = root / "experiments/event-070-b-pattern1-plain-playback"
    observation_path = source_folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    source_capture = source_folder / "capture.wav"
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(source_capture) != observation["capture_sha256"]
    ):
        raise ValueError("Accepted unchanged playback source required")
    source = load_artifact(source_path)
    base = decode_artifact(source)
    original = source.to_bytes()
    edited = rebuild_labels(source, fixed_up_packets(base))
    edited.metadata["transformations"].append(
        {
            "kind": "research-fixed-Pattern1-footer6-global7-preserved",
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    checks = footer_only_checks(base, target)
    if not all(checks.values()):
        raise ValueError("Fixed footer6 native preservation failed")
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
        entire_native_target_after_waveform_decode=actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        source_unchanged=source.to_bytes() == original
        and sha256_file(source_path) == observation["artifact_sha256"],
    )
    validation_path = folder / "software-validation.json"
    write_bytes(
        validation_path,
        json_bytes(
            {
                "analysis_version": "fixed-footer6-with-global7-software-validation-0.1",
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
        raise ValueError("Footer6 waveform failed; outputs retained")
    recorded_up_path = (
        root / "experiments/event-065-a-pattern1-FX7-recorded/hardware-observation-001.json"
    )
    recorded_up = json.loads(recorded_up_path.read_text())
    if not recorded_up["hardware_verified"] or not all(recorded_up["checks"].values()):
        raise ValueError("Earlier physical octave-up observation required")
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "generated-footer6-global7-octave-up-preregistration-0.1",
                "hardware_verified": False,
                "registered_before_generated_restore_capture": True,
                "experiment_id": DIRECTORY,
                "source_artifact": observation["artifact_path"],
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": source_capture.relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": SOURCE_BODY,
                "source_observation": observation_path.relative_to(root).as_posix(),
                "source_observation_sha256": sha256_file(observation_path),
                "expected_footer_hex": "6666666666666666",
                "expected_global131": 7,
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": sha256_file(folder / "restore.wav"),
                "software_validation_sha256": sha256_file(validation_path),
                "earlier_recorded_up_observation": recorded_up_path.relative_to(root).as_posix(),
                "earlier_recorded_up_observation_sha256": sha256_file(recorded_up_path),
                "hypothesis": "Uniform footer6 alone restores the user-recognized octave-up effect while global131 remains7 rather than recorded-up9",
                "limits": [
                    "Fixed exact-source research constructor only; no public FX writer or complete enum",
                    "Uniform footer cannot determine nibble order",
                    "Native acceptance and audible octave-up are separate checks; do not infer listening from bytes",
                    "Receive backup must precede listening playback to test exact target without new playback intervention",
                    "Even a successful test would not identify the global byte's role or prove it irrelevant to all effects",
                ],
            }
        ),
    )
    actions = [
        "Restore restore.wav using established stereo playback settings; leave both knobs untouched",
        "With playback stopped and write off, record a new complete capture.wav BEFORE listening playback",
        "With write off, play Pattern1 briefly and report whether the octave-up effect is audible, including uncertainty; stop afterward",
        "No FX button, write pass, knob movement or separate playback recording required",
    ]
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_restore_and_preplayback_capture",
                "restore_file": "restore.wav",
                "registration": "../" + REGISTRATION,
                "hardware_restore": {"status": "not_run"},
                "planned_actions": actions,
            }
        ),
    )
    write_bytes(
        folder / "instructions.md",
        (
            "# Fixed octave-up restore\n\n"
            + "\n".join(f"{i}. {action}" for i, action in enumerate(actions, 1))
            + "\n\nUse the established reduced capture level and one second trailing silence.\n"
        ).encode(),
    )
    print(
        json.dumps(
            {
                "passed": True,
                "restore": DIRECTORY + "/restore.wav",
                "target_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
