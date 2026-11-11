"""Register the melodic keyboard scale map: Sound3 key s on step s, measured by pitch.

From the verified writer-test state (16 Sound3 notes, 60 BPM, swing 0), Pattern 1's
effects are cleared and step s's auxiliary byte is set to F0 | (s - 1), so key s plays on
step s. Keys 1, 2, 7 and 16 already restored with these auxiliary values in earlier
tests; the other twelve follow the same low-nibble pattern. Every note keeps the same
primary bytes. The frozen frequency method measures each note, and the registered models
are chromatic, major and natural minor; the measured table is reported either way.
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
from scripts.pattern1_key_scale_method import MODELS, SETTINGS

SOURCE_EXPERIMENT = "compiled-step-effects-writer-001"
DIRECTORY = "edited-pattern1-key-scale-map-001"
REGISTRATION = "pattern1-key-scale-map-registration-001.json"
SOUND3_CELL = 2
PLAYBACK_SECONDS = 22
QUESTION = "Did the 16 notes rise steadily, and did any sound wrong? (Enter to skip)"
METHOD_FILES = {
    "key_scale_script_sha256": "scripts/pattern1_key_scale_method.py",
    "note_gate_script_sha256": "scripts/pattern1_fx_note_gate_method.py",
    "grid_script_sha256": "scripts/pattern1_fx_grid_pitch_method.py",
    "step1_script_sha256": "scripts/pattern1_fx_step_pitch_method.py",
}


def scale_pattern(original):
    data = bytearray(original)
    for step in range(1, 17):
        p = 48 * (step - 1) + 3 * SOUND3_CELL
        a = 768 + 16 * (step - 1) + SOUND3_CELL
        if original[p : p + 3] != bytes.fromhex("0e0981") or original[a] != 0xF0:
            raise ValueError(f"Step {step} must hold the calibrated Sound3 note with key 1")
        data[a] = 0xF0 | (step - 1)
    data[1024:] = bytes([0xFF]) * 8
    return bytes(data)


def scale_checks(base, actual):
    source, data = pattern_data(base, 1), pattern_data(actual, 1)
    restored = _replace_pattern_data(actual, 1, source)
    aux_offsets = {768 + 16 * (s - 1) + SOUND3_CELL for s in range(1, 17)}
    return {
        "source_and_actual_native_valid": all(
            encode_packets(frame.packets) == frame.encoded_body for frame in (base, actual)
        ),
        "only_Pattern1_changed": restored == base.packets,
        "only_Sound3_aux_bytes_and_footer_changed": all(
            data[i] == source[i] for i in range(1024) if i not in aux_offsets
        ),
        "key_s_on_step_s": all(
            data[768 + 16 * (s - 1) + SOUND3_CELL] == 0xF0 | (s - 1) for s in range(1, 17)
        ),
        "effects_cleared": data[1024:] == bytes([0xFF]) * 8,
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
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified writer-test state is required")
    source = load_artifact(source_path)
    base = decode_artifact(source)
    edited = rebuild_labels(
        source, _replace_pattern_data(base, 1, scale_pattern(pattern_data(base, 1)))
    )
    edited.metadata["transformations"].append(
        {"kind": "research-Sound3-key-scale-map", "hardware_verified": False}
    )
    target = decode_artifact(edited)
    checks = scale_checks(base, target)
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
                "analysis_version": "key-scale-map-native-and-waveform-validation-0.1",
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
                "analysis_version": "key-scale-map-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": sha256_file(restore),
                "method_settings": SETTINGS,
                **{key: sha256_file(root / path) for key, path in METHOD_FILES.items()},
                "models_cents": MODELS,
                "decision": [
                    "The backup must equal the target exactly",
                    "Each step's pitch is the median of its notes over five loops; intervals are cents relative to step 1",
                    "A model holds when all 16 steps are within 20 cents in the median and in at least 4 of 5 loops",
                    "Otherwise other_or_inconclusive; the measured interval table is reported either way",
                ],
                "limits": [
                    "Sound3 with its recorded parameters only; other sounds may differ",
                    "Measures pitch only, not note length or level",
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
    print(json.dumps({"ready": True, "folder": DIRECTORY}))


if __name__ == "__main__":
    main()
