"""Validate the genuine Sound2 removal without weakening the cell-copy checks."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.validate_sound_cell_recapture import comparison_checks as cell_checks


def comparison_checks(original, target, actual, registration):
    checks, packets, changes, sound2_steps, keys = cell_checks(
        original, target, actual, registration
    )
    del checks["source_sound2_cell_unchanged"]  # Removal intentionally clears the original cell.
    before, after = (
        pattern_data(original, registration["expected_pattern"]),
        pattern_data(actual, registration["expected_pattern"]),
    )
    checks["removed_sound2_cells_empty"] = all(
        after[48 * (step - 1) + 3 : 48 * (step - 1) + 6] == bytes(3)
        and after[768 + 16 * (step - 1) + 1] == 0
        for step in registration["expected_removed_sound2_steps"]
    )
    checks["remaining_sound2_cells_unchanged"] = all(
        before[48 * (step - 1) + 3 : 48 * (step - 1) + 6]
        == after[48 * (step - 1) + 3 : 48 * (step - 1) + 6]
        and before[768 + 16 * (step - 1) + 1] == after[768 + 16 * (step - 1) + 1]
        for step in registration["expected_sound2_steps"]
    )
    return checks, packets, changes, sound2_steps, keys


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-sound2-remove-001"
    registration_path = directory / "restore-registration.json"
    registration = json.loads(registration_path.read_text())
    source_path = directory / registration["source_artifact"]
    target_path = directory / registration["generated_artifact"]
    restore_path = directory / registration["restore_wav"]
    actual_path = directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    output = directory / "hardware-validation.json"
    validate_outputs(
        [output],
        [registration_path, source_path, target_path, restore_path, actual_path, capture],
        False,
    )
    artifacts = [load_artifact(p) for p in (source_path, target_path, actual_path)]
    if sha256_file(source_path) != registration["source_artifact_sha256"]:
        raise ValueError("Original artifact does not match registration")
    if artifacts[0].metadata["source_sha256"] != registration["source_backup_sha256"]:
        raise ValueError("Original artifact does not match registered source WAV")
    if artifacts[2].metadata["source_sha256"] != sha256_file(capture):
        raise ValueError("Recapture artifact does not match its WAV")
    if sha256_file(restore_path) != registration["restore_wav_sha256"]:
        raise ValueError("Restore WAV does not match registration")
    frames = [decode_artifact(a) for a in artifacts]
    checks, packets, changes, steps, keys = comparison_checks(*frames, registration)
    report = {
        "analysis_version": "native-sound2-cell-removal-hardware-validation-0.1",
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(actual_path),
        "decoder_version": artifacts[2].metadata["decoder_version"],
        "checks": checks,
        "passed": all(checks.values()),
        "native_frame": frame_report(frames[2]),
        "changed_plain_packet_indices": packets,
        "pattern1_byte_changes": changes,
        "sound2_steps": steps,
        "sound3_keys_by_step": keys,
        "user_report": "done and confirmed",
        "hardware_verified": all(checks.values()),
        "manual_observations": "User confirms Sound2 Step1 off, only Step9 lit, Sound3 Steps1/5/9/13 lit and normal playback; no deviation reported",
        "capture_timing": "Requested before step inspection and playback; user reports completion without a deviation",
        "limits": [
            "Light/playback observations are user reported; acoustic waveforms were not independently measured",
            "Only deletion of the observed Sound2 cell with calibrated optional Sound3 neighbours is validated locally",
            "Other sounds and Sound2 keys remain unsupported; primary note parameters remain opaque",
        ],
    }
    write_bytes(output, json_bytes(report))
    if not report["passed"]:
        raise ValueError("Sound2 removal recapture checks failed; report retained")


if __name__ == "__main__":
    main()
