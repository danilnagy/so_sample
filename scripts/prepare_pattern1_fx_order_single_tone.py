"""Register an F6/6F effect-order pair on the verified single-tone pattern.

Pattern 1 holds one Sound3 note on step 1 and nothing else. Footer byte 0 carries the
effect nibbles for steps 1 and 2. Leg A writes F6 and leg B writes 6F; every other byte,
including global byte 131 = 7, stays exactly as in the verified single-tone backup.
Only step 1 has a note, so only step 1's nibble is audible, and the frozen first-tone
window (80..140 ms after onset) lies inside step 1 at 100 BPM (150 ms per step).

Predictions are registered here, before any capture:
- low nibble first: A (F6) plays step 1 an octave up, B (6F) plays it unshifted
- high nibble first: A plays it unshifted, B an octave up
The primary decision is the frozen A/B first-tone ratio (2 or 0.5 within 1%). A second
registered check compares each leg with the measured unshifted single-tone reference.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, rebuild_labels
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_fx_nibble_audio import PARAMETERS

SOURCE_EXPERIMENT = "edited-pattern1-single-tone-no-FX-001"
SOURCE_BODY = "a97e89da4ebdc2bb236209d0ef295a1473e6a58757cca0165c466c4c667602a6"
REGISTRATION = "pattern1-single-tone-FX-order-registration-001.json"
LEGS = {
    "a": {"directory": "edited-pattern1-single-tone-FX-F6-001", "footer_byte": 0xF6},
    "b": {"directory": "edited-pattern1-single-tone-FX-6F-001", "footer_byte": 0x6F},
}
REFERENCE_RELATIVE_TOLERANCE = 0.01
PLAYBACK_SECONDS = 14
QUESTION = "Describe the pitch of the repeating tone, if you noticed it (Enter to skip)"


def leg_pattern(original, footer_byte):
    """The single-tone pattern with footer byte 0 set and the other seven left as F."""
    if original[1024:] != bytes([0xFF]) * 8:
        raise ValueError("Effects must be clear in the source pattern")
    occupied = [i for i in range(256) if any(original[3 * i : 3 * i + 3]) or original[768 + i]]
    if occupied != [2] or original[6:9] != bytes.fromhex("0e0981") or original[770] != 0xF0:
        raise ValueError("Exactly the single Sound3 step 1 note is required")
    data = bytearray(original)
    data[1024] = footer_byte
    return bytes(data)


def leg_checks(base, actual, footer_byte):
    """Native checks for one leg against the single-tone source frame."""
    source = pattern_data(base, 1)
    data = pattern_data(actual, 1)
    reverted = _replace_pattern_data(actual, 1, source)
    return {
        "source_is_verified_single_tone_body": hashlib.sha256(base.encoded_body).hexdigest()
        == SOURCE_BODY,
        "source_and_actual_native_valid": all(
            encode_packets(frame.packets) == frame.encoded_body for frame in (base, actual)
        )
        and len(base.packets) == len(actual.packets),
        "only_Pattern1_data_changed": reverted == base.packets,
        "only_footer_byte0_changed": data[:1024] == source[:1024]
        and data[1025:] == source[1025:]
        and data[1024] == footer_byte,
        "single_Sound3_step1_note_preserved": data[6:9] == bytes.fromhex("0e0981")
        and data[770] == 0xF0,
        "global131_preserved_at7": base.packets[2].payload[131]
        == actual.packets[2].payload[131]
        == 7,
    }


def reference_frequency(results):
    values = [
        m["fit"]["frequency_hz"]
        for channel in ("left", "right")
        for m in results["channels"][channel]["measurements"]
    ]
    if len(values) != 6 or not results["passed"]:
        raise ValueError("The single-tone reference needs six usable measurements")
    return float(np.mean(values)), values


def build_leg(root, source, base, leg, spec, reference_hz):
    folder = root / "experiments" / spec["directory"]
    edited = rebuild_labels(
        source,
        _replace_pattern_data(base, 1, leg_pattern(pattern_data(base, 1), spec["footer_byte"])),
    )
    edited.metadata["transformations"].append(
        {
            "kind": "research-single-tone-footer-byte0",
            "footer_byte0": f"{spec['footer_byte']:02X}",
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    checks = leg_checks(base, target, spec["footer_byte"])
    if not all(checks.values()):
        raise ValueError(f"Leg {leg}: native preservation failed: {checks}")
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    folder.mkdir()
    write_bytes(folder / "edited.symbols.npz", edited.to_bytes())
    pending = folder / "restore.unverified.wav"
    write_bytes(pending, waveform)
    recovered = decode_wav(pending, 0.02)
    write_bytes(folder / "redecoded.symbols.npz", recovered.to_bytes())
    phase = compare_artifacts(edited, recovered)
    actual = decode_artifact(recovered)
    checks.update(
        strict_phase_roundtrip=phase["passed"],
        entire_native_target_after_waveform_decode=actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
    )
    passed = all(checks.values())
    restore = folder / ("restore.wav" if passed else "restore.FAILED.wav")
    os.replace(pending, restore)
    write_bytes(
        folder / "software-validation.json",
        json_bytes(
            {
                "analysis_version": "single-tone-FX-order-leg-native-and-waveform-validation-0.1",
                "hardware_verified": False,
                "leg": leg,
                "passed": passed,
                "checks": checks,
                "encoding": encoding,
                "target_frame": frame_report(target),
                "strict_phase_roundtrip": phase,
            }
        ),
    )
    if not passed:
        raise ValueError(f"Leg {leg}: waveform checks failed; restore.FAILED.wav kept")
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": spec["directory"],
                "leg": leg,
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../" + REGISTRATION,
                "playback_seconds": PLAYBACK_SECONDS,
                "observation_questions": [QUESTION],
                "hardware_restore": {"status": "not_run"},
            }
        ),
    )
    other = "b" if leg == "a" else "a"
    write_bytes(
        folder / "instructions.md",
        (
            f"# Single-tone effect order, leg {leg.upper()} (footer byte "
            f"{spec['footer_byte']:02X})\n\n"
            f"Run leg {'A first' if leg == 'a' else 'B after leg A has passed'}:\n\n"
            "```powershell\n"
            f".\\.venv\\Scripts\\python.exe -m po33_re hw run experiments/{spec['directory']}\n"
            "```\n\n"
            "Follow the prompts: restore with only the computer-to-PO-33 cable connected, swap\n"
            "cables, send the backup, then press Enter and PLAY about one second later for the\n"
            "14-second playback. Do not press FX, enable write, or move knobs or volumes.\n"
            f"Leg {other.upper()} uses the same steps.\n"
        ).encode(),
    )
    return {
        "directory": spec["directory"],
        "footer_byte0": f"{spec['footer_byte']:02X}",
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
        "restore_wav_sha256": sha256_file(restore),
        "software_validation_sha256": sha256_file(folder / "software-validation.json"),
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    folders = [root / "experiments" / spec["directory"] for spec in LEGS.values()]
    if any(path.exists() for path in (registration_path, *folders)):
        raise ValueError("Fresh leg folders and registration required")
    source_folder = root / "experiments" / SOURCE_EXPERIMENT
    observation_path = source_folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    audio_path = source_folder / "first-tone-results-001.json"
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(audio_path) != observation["audio_results_sha256"]
    ):
        raise ValueError("The verified single-tone backup and its audio result are required")
    reference_hz, reference_values = reference_frequency(json.loads(audio_path.read_text()))
    source = load_artifact(source_path)
    before = source.to_bytes()
    base = decode_artifact(source)
    if hashlib.sha256(base.encoded_body).hexdigest() != SOURCE_BODY:
        raise ValueError("Source body differs from the verified single-tone body")
    legs = {
        leg: build_leg(root, source, base, leg, spec, reference_hz) for leg, spec in LEGS.items()
    }
    if source.to_bytes() != before or sha256_file(source_path) != observation["artifact_sha256"]:
        raise ValueError("Source artifact changed during preparation")
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "single-tone-FX-order-pair-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "source_experiment": SOURCE_EXPERIMENT,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": SOURCE_BODY,
                "source_observation_sha256": sha256_file(observation_path),
                "reference_audio_results_sha256": observation["audio_results_sha256"],
                "reference_frequency_hz": reference_hz,
                "reference_measurements_hz": reference_values,
                "reference_relative_tolerance": REFERENCE_RELATIVE_TOLERANCE,
                "legs": legs,
                "capture_order": ["a", "b"],
                "audio_parameters": PARAMETERS,
                "audio_method_script_sha256": sha256_file(
                    root / "scripts/pattern1_fx_nibble_audio.py"
                ),
                "frequency_fit_helper_sha256": sha256_file(
                    root / "scripts/sound3_pitch_frequency_analysis.py"
                ),
                "predictions": {
                    "low_nibble_first": {
                        "a_over_b_ratio": 2.0,
                        "a_frequency_hz": 2 * reference_hz,
                        "b_frequency_hz": reference_hz,
                    },
                    "high_nibble_first": {
                        "a_over_b_ratio": 0.5,
                        "a_frequency_hz": reference_hz,
                        "b_frequency_hz": 2 * reference_hz,
                    },
                },
                "decision": [
                    "Both legs must be received exactly; only footer byte 0 may differ from the source",
                    "Primary: the frozen comparison of all six A/B first-tone ratios, near 2 or near 0.5 within the registered 1% tolerance",
                    "Secondary: each leg's six first tones must match its model's predicted frequency within 1% of the registered reference",
                    "A model is supported only if primary and secondary agree; anything else stays inconclusive",
                ],
                "earlier_lead": "The earlier F6 restore's first tone (about 1190.65 Hz) matched the unshifted reference, suggesting high nibble first; it was not registered and does not count here",
                "limits": [
                    "Local to footer byte 0 of Pattern 1 with one Sound3 note on step 1; not an all-step or all-pattern ordering",
                    "Octave up is the only effect code used; no general per-step effect writer is enabled",
                    "No retuning of the frozen first-tone method after data; failed or unusable results are retained",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "legs": {k: v["directory"] for k, v in legs.items()}}))


if __name__ == "__main__":
    main()
