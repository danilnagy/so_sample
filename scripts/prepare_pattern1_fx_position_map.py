"""Register a footer position map: four equal notes, the rising effect on steps 5 and 13.

Built from the verified single-tone backup. Pattern 1 gets the existing Sound3 note
(primary 0e0981, auxiliary F0) on steps 1, 5, 9 and 13; the same four-step Sound3
layout was restored and recaptured exactly earlier. The footer is FF FF 6F FF FF FF 6F
FF: under the sequential model (byte k holds steps 2k+1 and 2k+2, high nibble first, as
confirmed for byte 0) the effect falls on steps 5 and 13 only.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report, rebuild_labels
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_fx_multi_step_pitch_method import SETTINGS

SOURCE_EXPERIMENT = "edited-pattern1-single-tone-no-FX-001"
SOURCE_BODY = "a97e89da4ebdc2bb236209d0ef295a1473e6a58757cca0165c466c4c667602a6"
DIRECTORY = "edited-pattern1-FX-position-map-001"
REGISTRATION = "pattern1-FX-position-map-registration-001.json"
NOTE_STEPS = (1, 5, 9, 13)
FOOTER = bytes.fromhex("ffff6fffffff6fff")
PLAYBACK_SECONDS = 14
QUESTION = "Which of the four notes, if any, bent upward? (Enter to skip)"
PREDICTIONS = {
    "sequential_high_nibble_first": {"1": "none", "5": "effect", "9": "none", "13": "effect"},
    "effect_on_no_note_step": {"1": "none", "5": "none", "9": "none", "13": "none"},
}


def position_map_pattern(original):
    if original[1024:] != bytes([0xFF]) * 8:
        raise ValueError("Effects must be clear in the source pattern")
    occupied = [i for i in range(256) if any(original[3 * i : 3 * i + 3]) or original[768 + i]]
    if occupied != [2] or original[6:9] != bytes.fromhex("0e0981") or original[770] != 0xF0:
        raise ValueError("Exactly the single Sound3 step 1 note is required")
    data = bytearray(original)
    for step in NOTE_STEPS[1:]:
        p, a = 48 * (step - 1), 768 + 16 * (step - 1)
        data[p : p + 48] = original[0:48]
        data[a : a + 16] = original[768:784]
    data[1024:] = FOOTER
    return bytes(data)


def position_map_checks(base, actual):
    source = pattern_data(base, 1)
    data = pattern_data(actual, 1)
    reverted = _replace_pattern_data(actual, 1, source)
    occupied = [i for i in range(256) if any(data[3 * i : 3 * i + 3]) or data[768 + i]]
    return {
        "source_is_verified_single_tone_body": hashlib.sha256(base.encoded_body).hexdigest()
        == SOURCE_BODY,
        "source_and_actual_native_valid": all(
            encode_packets(frame.packets) == frame.encoded_body for frame in (base, actual)
        )
        and len(base.packets) == len(actual.packets),
        "only_Pattern1_data_changed": reverted == base.packets,
        "notes_exactly_on_steps_1_5_9_13": occupied == [16 * (s - 1) + 2 for s in NOTE_STEPS],
        "every_note_identical_to_step1": all(
            data[48 * (s - 1) : 48 * s] == source[0:48]
            and data[768 + 16 * (s - 1) : 768 + 16 * s] == source[768:784]
            for s in NOTE_STEPS
        ),
        "footer_exact": data[1024:] == FOOTER,
        "global131_preserved_at7": base.packets[2].payload[131]
        == actual.packets[2].payload[131]
        == 7,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if folder.exists() or registration_path.exists():
        raise ValueError("Fresh folder and registration required")
    source_folder = root / "experiments" / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or sha256_file(source_path) != observation["artifact_sha256"]
    ):
        raise ValueError("The verified single-tone backup is required")
    first_registration = json.loads(
        (root / "experiments/pattern1-single-tone-FX-order-registration-001.json").read_text()
    )
    confirmation = json.loads(
        (
            root / "experiments/pattern1-single-tone-FX-order-pitch-track-decision-001.json"
        ).read_text()
    )
    if confirmation["classification"] != "high_nibble_first":
        raise ValueError("The byte-0 high-nibble-first confirmation is required")
    source = load_artifact(source_path)
    base = decode_artifact(source)
    edited = rebuild_labels(
        source, _replace_pattern_data(base, 1, position_map_pattern(pattern_data(base, 1)))
    )
    edited.metadata["transformations"].append(
        {
            "kind": "research-four-note-FX-position-map",
            "footer": FOOTER.hex(),
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    checks = position_map_checks(base, target)
    if not all(checks.values()):
        raise ValueError(f"Native preservation failed: {checks}")
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
                "analysis_version": "FX-position-map-native-and-waveform-validation-0.1",
                "hardware_verified": False,
                "passed": passed,
                "checks": checks,
                "encoding": encoding,
                "target_frame": frame_report(target),
                "strict_phase_roundtrip": phase,
            }
        ),
    )
    if not passed:
        raise ValueError("Waveform checks failed; restore.FAILED.wav kept")
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "FX-position-map-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": SOURCE_BODY,
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": sha256_file(restore),
                "software_validation_sha256": sha256_file(folder / "software-validation.json"),
                "note_steps": list(NOTE_STEPS),
                "footer": FOOTER.hex(),
                "reference_frequency_hz": first_registration["reference_frequency_hz"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_fx_multi_step_pitch_method.py"
                ),
                "step1_method_script_sha256": sha256_file(
                    root / "scripts/pattern1_fx_step_pitch_method.py"
                ),
                "predictions": PREDICTIONS,
                "decision": [
                    "The backup must equal the target exactly; only Pattern 1 may differ from the single-tone source",
                    "Each note is classified 20-130 ms after its onset with the frozen step-1 thresholds",
                    "A prediction holds only if exactly steps 1, 5, 9 and 13 are found and each matches in its five-loop median and at least 4 of 5 loops",
                    "Anything else is inconclusive; no retuning after data",
                ],
                "builds_on": [
                    "experiments/pattern1-single-tone-FX-order-pitch-track-decision-001.json",
                    "docs/generated-pattern1-FX-mixed-results.md",
                ],
                "limits": [
                    "Tests footer bytes 0, 2, 4 and 6 high nibbles through four notes; low nibbles of bytes 1..7 are inferred, not observed",
                    "Pattern 1 and effect code 6 only; no general per-step effect writer is enabled",
                ],
            }
        ),
    )
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
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
    write_bytes(
        folder / "instructions.md",
        (
            "# Effect position map\n\n"
            "```powershell\n"
            f".\\.venv\\Scripts\\python.exe -m po33_re hw run experiments/{DIRECTORY}\n"
            ".\\.venv\\Scripts\\python.exe -m scripts.check_pattern1_fx_position_map\n"
            "```\n"
        ).encode(),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
