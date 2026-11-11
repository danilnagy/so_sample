"""Register a single existing Sound3 trigger with clear FX and the unchanged first-tone method."""

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

SOURCE_BODY = "a16872e153dd2fd3dfce98bc47a8aed085113b537658aabf92fc4719e385716b"
DIRECTORY = "edited-pattern1-single-tone-no-FX-001"
REGISTRATION = "pattern1-single-tone-FX-order-baseline-registration-001.json"


def single_tone_pattern(frame):
    if hashlib.sha256(frame.encoded_body).hexdigest() != SOURCE_BODY:
        raise ValueError("Exact accepted first-pair B source required")
    original = pattern_data(frame, 1)
    if original[6:9] != bytes.fromhex("0e0981") or original[770] != 0xF0:
        raise ValueError("Existing calibrated Sound3 step1 trigger required")
    data = bytearray(1024) + bytearray([0xFF]) * 8
    data[6:9] = original[6:9]
    data[770] = original[770]
    return bytes(data)


def fixed_baseline_packets(frame):
    return _replace_pattern_data(frame, 1, single_tone_pattern(frame))


def baseline_checks(base, actual):
    source_ok = hashlib.sha256(base.encoded_body).hexdigest() == SOURCE_BODY
    source_data = pattern_data(base, 1)
    actual_data = pattern_data(actual, 1)
    reverted = _replace_pattern_data(actual, 1, source_data)
    return {
        "source_is_exact_accepted_B_body": source_ok,
        "source_and_actual_native_valid": all(
            len(frame.packets) == 815
            and frame.end_byte == 156758
            and encode_packets(frame.packets) == frame.encoded_body
            for frame in (base, actual)
        ),
        "only_Pattern1_data_changed": reverted == base.packets,
        "entire_single_tone_pattern_exact": source_ok and actual_data == single_tone_pattern(base),
        "existing_Sound3_step1_cell_preserved": actual_data[6:9] == source_data[6:9]
        and actual_data[770] == source_data[770],
        "all_effects_clear": actual_data[1024:] == bytes([0xFF]) * 8,
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
        raise ValueError("Fresh single-tone baseline folder and registration required")
    source_folder = root / "experiments/edited-pattern1-FX-6F-first-pair-001"
    observation_path = source_folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    comparison_path = root / "experiments/pattern1-FX-first-pair-audio-comparison-001.json"
    comparison = json.loads(comparison_path.read_text())
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(source_folder / "capture.wav") != observation["capture_sha256"]
        or comparison["comparison_usable"]
        or comparison["classification"] != "inconclusive"
    ):
        raise ValueError("Accepted native B and retained inconclusive audio result required")
    source = load_artifact(source_path)
    before = source.to_bytes()
    base = decode_artifact(source)
    edited = rebuild_labels(source, fixed_baseline_packets(base))
    edited.metadata["transformations"].append(
        {"kind": "research-single-existing-Sound3-trigger-clear-FX", "hardware_verified": False}
    )
    target = decode_artifact(edited)
    checks = baseline_checks(base, target)
    if not all(checks.values()):
        raise ValueError("Single-tone native preservation failed")
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    folder.mkdir()
    write_bytes(folder / "edited.symbols.npz", edited.to_bytes())
    write_bytes(folder / "restore.wav", waveform)
    recovered = decode_wav(folder / "restore.wav", 0.02)
    write_bytes(folder / "redecoded.symbols.npz", recovered.to_bytes())
    actual = decode_artifact(recovered)
    phase = compare_artifacts(edited, recovered)
    checks.update(
        strict_phase_roundtrip=phase["passed"],
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
                "analysis_version": "single-tone-baseline-native-and-waveform-validation-0.1",
                "hardware_verified": False,
                "passed": all(checks.values()),
                "checks": checks,
                "encoding": encoding,
                "target_frame": frame_report(target),
                "strict_phase_roundtrip": phase,
            }
        ),
    )
    if not all(checks.values()):
        raise ValueError("Single-tone waveform failed; outputs retained")
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "new-single-tone-baseline-after-inconclusive-order-probe-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": observation["artifact_path"],
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (source_folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_observation": observation_path.relative_to(root).as_posix(),
                "source_observation_sha256": sha256_file(observation_path),
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": sha256_file(folder / "restore.wav"),
                "software_validation_sha256": sha256_file(validation_path),
                "earlier_inconclusive_comparison_sha256": sha256_file(comparison_path),
                "audio_parameters": PARAMETERS,
                "audio_method_script_sha256": sha256_file(
                    root / "scripts/pattern1_fx_nibble_audio.py"
                ),
                "frequency_fit_helper_sha256": sha256_file(
                    root / "scripts/sound3_pitch_frequency_analysis.py"
                ),
                "expected_reference_frequency_hz": None,
                "hypothesis": "One preserved Sound3 step1 trigger with all other Pattern1 cells empty and FX clear yields a usable first tone under the unchanged frozen method",
                "limits": [
                    "Changes the entire Pattern1 cell region to one existing trigger; all samples, other15 patterns and globals remain exact",
                    "New source calibration is registered after the prior failed audio-quality check, before these new captures; prior recordings and results are unchanged",
                    "Does not retune the failed first-tone method or adjudicate the previous F6/6F order hypotheses",
                    "Native reception and audio usability must pass before preparing any new effect-order pair",
                    "No guessed reference frequency, audible octave ratio, general note editor or per-step effect writer",
                ],
            }
        ),
    )
    actions = [
        "Restore restore.wav with usual stereo settings; keep write off and both knobs untouched",
        "Before playing, record full capture.wav at the same reduced level with one second trailing silence",
        "Start a separate playback.wav recording, leave about one second silence, then press PLAY; record12 to15 seconds of Pattern1 and stop",
        "Confirm whether you hear one tone repeating per loop; do not trim leading silence or the first note, press FX, or move knobs",
    ]
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_single_tone_baseline_backup_and_audio",
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
            "# Single-tone measurement baseline\n\n"
            + "\n".join(f"{i}. {action}" for i, action in enumerate(actions, 1))
            + "\n"
        ).encode(),
    )
    print(json.dumps({"ready": True, "restore": DIRECTORY + "/restore.wav"}))


if __name__ == "__main__":
    main()
