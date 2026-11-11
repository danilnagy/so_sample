"""Register a full 16-step effect position map at 60 BPM.

From the verified single-tone backup: the existing Sound3 note on all 16 steps of
Pattern 1, tempo 60 BPM (250 ms steps, so 210 ms notes do not overlap) and swing 0 (so
every step starts on time). Both values are inside the hardware-verified tempo and
swing ranges. The rising effect code 6 sits on steps 2, 3, 5, 6, 10, 11, 13 and 14:
footer F6 6F 66 FF F6 6F 66 FF, which gives every byte a different high/low combination.
Notes are found on the step grid (pattern1_fx_grid_pitch_method.py) and classified with
the frozen step-1 rule; grouping and the decision come from the multi-step module.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import (
    Packet,
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
from scripts.pattern1_fx_grid_pitch_method import SETTINGS

SOURCE_EXPERIMENT = "edited-pattern1-single-tone-no-FX-001"
SOURCE_BODY = "a97e89da4ebdc2bb236209d0ef295a1473e6a58757cca0165c466c4c667602a6"
DIRECTORY = "edited-pattern1-FX-full-step-map-001"
REGISTRATION = "pattern1-FX-full-step-map-registration-001.json"
FOOTER = bytes.fromhex("f66f66fff66f66ff")
EFFECT_STEPS = (2, 3, 5, 6, 10, 11, 13, 14)
TEMPO_BPM, SWING = 60, 0
GLOBAL_RECORD_INDEX, TEMPO_OFFSET, SWING_OFFSET = 2, 129, 130
PLAYBACK_SECONDS = 22
QUESTION = "Roughly which notes bent upward, if you could tell? (Enter to skip)"


def nibble_steps(footer, high_first):
    steps = []
    for k, byte in enumerate(footer):
        first, second = (byte >> 4, byte & 15) if high_first else (byte & 15, byte >> 4)
        for offset, code in enumerate((first, second)):
            if code == 6:
                steps.append(2 * k + 1 + offset)
    return steps


PREDICTIONS = {
    "sequential_high_nibble_first": {
        str(s): ("effect" if s in nibble_steps(FOOTER, True) else "none") for s in range(1, 17)
    },
    "sequential_low_nibble_first": {
        str(s): ("effect" if s in nibble_steps(FOOTER, False) else "none") for s in range(1, 17)
    },
}


def full_map_pattern(original):
    if original[1024:] != bytes([0xFF]) * 8:
        raise ValueError("Effects must be clear in the source pattern")
    occupied = [i for i in range(256) if any(original[3 * i : 3 * i + 3]) or original[768 + i]]
    if occupied != [2] or original[6:9] != bytes.fromhex("0e0981") or original[770] != 0xF0:
        raise ValueError("Exactly the single Sound3 step 1 note is required")
    data = bytearray(original)
    for step in range(2, 17):
        p, a = 48 * (step - 1), 768 + 16 * (step - 1)
        data[p : p + 48] = original[0:48]
        data[a : a + 16] = original[768:784]
    data[1024:] = FOOTER
    return bytes(data)


def edited_packets(frame):
    packets = list(_replace_pattern_data(frame, 1, full_map_pattern(pattern_data(frame, 1))))
    record = packets[GLOBAL_RECORD_INDEX]
    if record.tag != 0x7D5C:
        raise ValueError("Second global record not at the expected packet index")
    payload = bytearray(record.payload)
    payload[TEMPO_OFFSET], payload[SWING_OFFSET] = TEMPO_BPM, SWING
    packets[GLOBAL_RECORD_INDEX] = Packet(record.tag, bytes(payload))
    return tuple(packets)


def full_map_checks(base, actual):
    source = pattern_data(base, 1)
    data = pattern_data(actual, 1)
    restored = list(_replace_pattern_data(actual, 1, source))
    restored[GLOBAL_RECORD_INDEX] = base.packets[GLOBAL_RECORD_INDEX]
    old, new = (
        base.packets[GLOBAL_RECORD_INDEX].payload,
        actual.packets[GLOBAL_RECORD_INDEX].payload,
    )
    other_bytes_same = all(
        old[i] == new[i] for i in range(len(old)) if i not in (TEMPO_OFFSET, SWING_OFFSET)
    )
    return {
        "source_is_verified_single_tone_body": hashlib.sha256(base.encoded_body).hexdigest()
        == SOURCE_BODY,
        "source_and_actual_native_valid": all(
            encode_packets(frame.packets) == frame.encoded_body for frame in (base, actual)
        )
        and len(base.packets) == len(actual.packets),
        "only_Pattern1_and_tempo_swing_changed": tuple(restored) == base.packets
        and other_bytes_same,
        "note_on_every_step_identical_to_step1": all(
            data[48 * (s - 1) : 48 * s] == source[0:48]
            and data[768 + 16 * (s - 1) : 768 + 16 * s] == source[768:784]
            for s in range(1, 17)
        ),
        "footer_exact": data[1024:] == FOOTER,
        "tempo_60_swing_0": new[TEMPO_OFFSET] == TEMPO_BPM and new[SWING_OFFSET] == SWING,
        "pattern1_byte131_preserved": old[131] == new[131],
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
    position_map = json.loads(
        (root / "experiments/pattern1-FX-position-map-decision-001.json").read_text()
    )
    if position_map["classification"] != "sequential_high_nibble_first":
        raise ValueError("The confirmed position map is required")
    reference = json.loads(
        (root / "experiments/pattern1-single-tone-FX-order-registration-001.json").read_text()
    )["reference_frequency_hz"]
    source = load_artifact(source_path)
    base = decode_artifact(source)
    edited = rebuild_labels(source, edited_packets(base))
    edited.metadata["transformations"].append(
        {
            "kind": "research-16-note-FX-full-step-map",
            "footer": FOOTER.hex(),
            "tempo_bpm": TEMPO_BPM,
            "swing": SWING,
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    checks = full_map_checks(base, target)
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
                "analysis_version": "FX-full-step-map-native-and-waveform-validation-0.1",
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
                "analysis_version": "FX-full-step-map-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture_sha256": observation["capture_sha256"],
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": sha256_file(restore),
                "footer": FOOTER.hex(),
                "effect_steps": list(EFFECT_STEPS),
                "tempo_bpm": TEMPO_BPM,
                "swing": SWING,
                "reference_frequency_hz": reference,
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_fx_grid_pitch_method.py"
                ),
                "grouping_script_sha256": sha256_file(
                    root / "scripts/pattern1_fx_multi_step_pitch_method.py"
                ),
                "step1_method_script_sha256": sha256_file(
                    root / "scripts/pattern1_fx_step_pitch_method.py"
                ),
                "predictions": PREDICTIONS,
                "decision": [
                    "The backup must equal the target exactly; only Pattern 1 and the tempo and swing bytes may differ from the source",
                    "Each of the 16 notes is classified 20-130 ms after its onset with the frozen thresholds",
                    "A model holds only if all 16 steps are found and each matches in its five-loop median and at least 4 of 5 loops",
                    "Anything else is inconclusive; the observed per-step map is reported either way",
                ],
                "limits": [
                    "Pattern 1, effect code 6, tempo 60 and swing 0; other patterns and codes rely on the code map",
                    "No general per-step effect writer is enabled by this test alone",
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
    print(json.dumps({"ready": True, "folder": DIRECTORY, "effect_steps": list(EFFECT_STEPS)}))


if __name__ == "__main__":
    main()
