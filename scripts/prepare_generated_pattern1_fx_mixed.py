"""Register fixed four66/four77 footer bytes; per-step nibble order stays unconfirmed."""

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

SOURCE_BODY = "3d3762e28817a2bccf83986539c889d1e74e70139b2313affcc3d56cc1bb370b"
FOOTER = bytes([0x66]) * 4 + bytes([0x77]) * 4
DIRECTORY = "edited-pattern1-FX6-7-halves-global7-001"
REGISTRATION = "pattern1-generated-mixed-FX-halves-global7-registration-001.json"


def fixed_mixed_packets(frame):
    if hashlib.sha256(frame.encoded_body).hexdigest() != SOURCE_BODY:
        raise ValueError("Exact accepted clear/global7 source required")
    data = bytearray(pattern_data(frame, 1))
    data[1024:] = FOOTER
    return _replace_pattern_data(frame, 1, bytes(data))


def mixed_checks(base, actual):
    data = bytearray(pattern_data(actual, 1))
    footer_matches = data[1024:] == FOOTER
    data[1024:] = pattern_data(base, 1)[1024:]
    return {
        "source_is_exact_clear_body": hashlib.sha256(base.encoded_body).hexdigest() == SOURCE_BODY,
        "source_and_actual_native_valid": all(
            len(frame.packets) == 815
            and frame.end_byte == 156758
            and encode_packets(frame.packets) == frame.encoded_body
            for frame in (base, actual)
        ),
        "footer_is_fixed_6666666677777777": footer_matches,
        "only_eight_Pattern1_footer_bytes_changed": _replace_pattern_data(actual, 1, bytes(data))
        == base.packets,
        "global131_preserved_at7": base.packets[2].payload[131]
        == actual.packets[2].payload[131]
        == 7,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if any(path.exists() or path.is_symlink() for path in (folder, registration_path)):
        raise ValueError("Fresh mixed-effect folder and registration required")
    source_folder = root / "experiments/edited-pattern1-FX15-global7-clear-001"
    observation_path = source_folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(source_folder / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Accepted exact clear-return source required")
    source = load_artifact(source_path)
    before = source.to_bytes()
    base = decode_artifact(source)
    edited = rebuild_labels(source, fixed_mixed_packets(base))
    edited.metadata["transformations"].append(
        {"kind": "research-fixed-four66-four77-footer", "hardware_verified": False}
    )
    target = decode_artifact(edited)
    checks = mixed_checks(base, target)
    if not all(checks.values()):
        raise ValueError("Mixed native preservation failed")
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
        source_unchanged=source.to_bytes() == before
        and sha256_file(source_path) == observation["artifact_sha256"],
    )
    validation_path = folder / "software-validation.json"
    write_bytes(
        validation_path,
        json_bytes(
            {
                "analysis_version": "fixed-mixed-footer-global7-waveform-validation-0.1",
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
        raise ValueError("Mixed waveform failed; outputs retained")
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "mixed-effect-halves-global7-preregistration-0.1",
                "hardware_verified": False,
                "registered_before_physical_recapture": True,
                "experiment_id": DIRECTORY,
                "source_artifact": observation["artifact_path"],
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (source_folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_observation": observation_path.relative_to(root).as_posix(),
                "source_observation_sha256": sha256_file(observation_path),
                "source_body_sha256": SOURCE_BODY,
                "expected_footer_hex": FOOTER.hex(),
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": sha256_file(folder / "restore.wav"),
                "software_validation_sha256": sha256_file(validation_path),
                "low_nibble_first_values": [6] * 8 + [7] * 8,
                "high_nibble_first_values": [6] * 8 + [7] * 8,
                "hypothesis": "Mixed footer retains both effects and changes from octave-up in steps1..8 to octave-down in steps9..16",
                "limits": [
                    "Chronological block association is a new listening hypothesis, not established by native target equality",
                    "Both nibble orders predict identical halves; success cannot distinguish adjacent-step nibble order",
                    "Known notes have different pitches; report the audible change and uncertainty without assuming frequency ratios",
                    "Public effect edit plans still allow only uniform none/up/down in the exact calibrated context",
                    "No other globals, samples, notes, sound settings or parameter locks are modified; failed predictions remain retained",
                ],
            }
        ),
    )
    actions = [
        "Restore restore.wav using established stereo settings; leave both knobs untouched",
        "Stopped and write off: record complete capture.wav BEFORE playing",
        "With write off, play Pattern1 for several loops; report whether it switches between higher and lower sections, then stop",
        "Do not press FX or move knobs; use the same reduced recording level and one second trailing silence",
    ]
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_mixed_effect_restore_and_recapture",
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
            "# Mixed-effect restore\n\n"
            + "\n".join(f"{i}. {action}" for i, action in enumerate(actions, 1))
            + "\n"
        ).encode(),
    )
    print(json.dumps({"ready": True, "restore": DIRECTORY + "/restore.wav"}))


if __name__ == "__main__":
    main()
