"""Freeze complementary F6/6F first-byte restores and first-tone ratio alternatives."""

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
from scripts.pattern1_fx_nibble_audio import PARAMETERS

SOURCE_BODY = "301798098c33bd2d73186e673239467242f33116507acf5f4beb235e50e0c7b1"
REGISTRATION = "pattern1-generated-FX-first-pair-order-registration-001.json"
LEGS = {
    "a": ("edited-pattern1-FX-F6-first-pair-001", 0xF6),
    "b": ("edited-pattern1-FX-6F-first-pair-001", 0x6F),
}


def fixed_probe_packets(frame, leg):
    if leg not in LEGS or hashlib.sha256(frame.encoded_body).hexdigest() != SOURCE_BODY:
        raise ValueError("Exact accepted mixed source and fixed a/b leg required")
    data = bytearray(pattern_data(frame, 1))
    data[1024:] = bytes([LEGS[leg][1]]) + bytes([0xFF]) * 7
    return _replace_pattern_data(frame, 1, bytes(data))


def probe_checks(base, actual, leg):
    if leg not in LEGS:
        raise ValueError("Fixed a/b leg required")
    data = bytearray(pattern_data(actual, 1))
    footer_correct = data[1024:] == bytes([LEGS[leg][1]]) + bytes([0xFF]) * 7
    data[1024:] = pattern_data(base, 1)[1024:]
    return {
        "source_body_is_exact_accepted_mixed": hashlib.sha256(base.encoded_body).hexdigest()
        == SOURCE_BODY,
        "source_and_actual_native_valid": all(
            len(frame.packets) == 815
            and frame.end_byte == 156758
            and encode_packets(frame.packets) == frame.encoded_body
            for frame in (base, actual)
        ),
        "footer_matches_fixed_first_pair_probe": footer_correct,
        "only_eight_Pattern1_footer_bytes_changed": _replace_pattern_data(actual, 1, bytes(data))
        == base.packets,
        "global131_stays7": base.packets[2].payload[131] == actual.packets[2].payload[131] == 7,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    folders = [root / "experiments" / spec[0] for spec in LEGS.values()]
    if any(path.exists() or path.is_symlink() for path in [registration_path, *folders]):
        raise ValueError("Fresh first-pair registration and folders required")
    source_folder = root / "experiments/edited-pattern1-FX6-7-halves-global7-001"
    observation_path = source_folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(source_folder / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Accepted exact mixed capture required")
    source = load_artifact(source_path)
    base = decode_artifact(source)
    sequence = []
    for (leg, (_, byte)), folder in zip(LEGS.items(), folders):
        before = source.to_bytes()
        edited = rebuild_labels(source, fixed_probe_packets(base, leg))
        edited.metadata["transformations"].append(
            {"kind": "research-first-pair-FX-" + leg, "hardware_verified": False}
        )
        target = decode_artifact(edited)
        checks = probe_checks(base, target, leg)
        if not all(checks.values()):
            raise ValueError("First-pair native preservation failed")
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
            source_unchanged=source.to_bytes() == before
            and sha256_file(source_path) == observation["artifact_sha256"],
        )
        validation_path = folder / "software-validation.json"
        write_bytes(
            validation_path,
            json_bytes(
                {
                    "analysis_version": "fixed-first-pair-FX-waveform-validation-0.1",
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
            raise ValueError("First-pair waveform failed; outputs retained")
        sequence.append(
            {
                "leg": leg,
                "experiment_id": folder.name,
                "expected_footer_hex": (bytes([byte]) + bytes([255]) * 7).hex(),
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": sha256_file(folder / "restore.wav"),
                "software_validation_sha256": sha256_file(validation_path),
            }
        )
        actions = [
            "Restore restore.wav with established stereo settings; keep write off and both knobs untouched",
            "Before playing, record complete backup capture.wav at the established reduced level with one second trailing silence",
            "For separate ordinary pattern audio playback.wav, start recording while stopped, leave about one second silence, then press PLAY",
            "Record12 to15 seconds of Pattern1, then press PLAY to stop; do not press FX or enable write; preserve recording settings",
            "Do not trim the leading silence or first note; report any uncertainty or deviations",
        ]
        write_bytes(
            folder / "experiment.json",
            json_bytes(
                {
                    "experiment_id": folder.name,
                    "leg": leg,
                    "capture_status": "awaiting_first_pair_restore_backup_and_playback",
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
                "# Complementary first-pair probe "
                + leg.upper()
                + "\n\n"
                + "\n".join(f"{i}. {action}" for i, action in enumerate(actions, 1))
                + "\n"
            ).encode(),
        )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "first-pair-FX-nibble-order-and-first-tone-preregistration-0.1",
                "hardware_verified": False,
                "registered_before_both_native_and_playback_captures": True,
                "source_artifact": observation["artifact_path"],
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (source_folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_observation": observation_path.relative_to(root).as_posix(),
                "source_observation_sha256": sha256_file(observation_path),
                "expected_capture_sequence": sequence,
                "audio_parameters": PARAMETERS,
                "audio_method_script_sha256": sha256_file(
                    root / "scripts/pattern1_fx_nibble_audio.py"
                ),
                "frequency_fit_helper_sha256": sha256_file(
                    root / "scripts/sound3_pitch_frequency_analysis.py"
                ),
                "low_nibble_first_hypothesis": "A first pair is up/none, B none/up; first-tone frequency A/B near2",
                "high_nibble_first_hypothesis": "A first pair is none/up, B up/none; first-tone frequency A/B near0.5",
                "limits": [
                    "First PLAY must start from the restored stopped Pattern1 state; begin audio recording before PLAY so first tone is preserved",
                    "First audible tone must correspond to the same initial event in both restores; frequency fit quality alone cannot establish that association",
                    "One first byte differs; all remaining fourteen effect nibbles areF and every nonfooter byte including global7 is exact",
                    "Identical method for both recordings: broad fixed band/search, first qualifying tone only, three thresholds and both channels; never skip a failed first region to fit a later note",
                    "Both full native targets must pass before interpreting audio; six ratios near2 or0.5 support separate local hypotheses; other results stay inconclusive",
                    "No method retuning after new data, all-pattern generalization, full effect enum or general per-step writer",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "restore_folders": [folder.name for folder in folders]}))


if __name__ == "__main__":
    main()
