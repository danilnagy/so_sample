"""Classify the over-limit memory step from the backup, then measure Sound10 if accepted."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report, sound_data, sound_groups
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_memory_test import total_capacity
from scripts.pattern1_key_scale_grid_method import decide, intervals, step_frequencies
from scripts.prepare_sample_memory_step4 import (
    DIRECTORY,
    MODELS,
    REGISTRATION,
    SETTINGS,
    absolute_decision,
)

DECISION = "sample-memory-decision-004.json"


def buffers(frame):
    return {
        sid: len(sound_data(frame, sid)) - 9
        for sid, indices in sound_groups(frame).items()
        if indices and len(sound_data(frame, sid)) > 9
    }


def record(frame, sid):
    return sound_data(frame, sid) if sound_groups(frame).get(sid) else b""


def classify(actual, target, source):
    """Return the outcome name and a summary of how the backup relates to both states."""
    if actual is None:
        return "not_decoded", {}
    summary = {
        "total_capacity_codes": total_capacity(actual),
        "buffers": {str(k): v for k, v in buffers(actual).items()},
        "sound_ids_differing_from_target": sorted(
            sid
            for sid in set(sound_groups(actual)) | set(sound_groups(target))
            if record(actual, sid) != record(target, sid)
        ),
        "sound_ids_differing_from_source": sorted(
            sid
            for sid in set(sound_groups(actual)) | set(sound_groups(source))
            if record(actual, sid) != record(source, sid)
        ),
    }
    if actual.packets == target.packets and actual.encoded_body == target.encoded_body:
        return "accepted_exact", summary
    if actual.packets == source.packets and actual.encoded_body == source.encoded_body:
        return "kept_previous", summary
    if summary["total_capacity_codes"] == 0:
        return "empty", summary
    return "other", summary


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / "scripts/pattern1_key_scale_grid_method.py")
        != registration["method_script_sha256"]
    ):
        raise ValueError("Frozen method changed since registration")
    if registration["method_settings"] != SETTINGS or registration["models_cents"] != MODELS:
        raise ValueError("Frozen settings or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    source_path = root / registration["source_artifact"]
    native_path = folder / "hardware-recapture-results-001.json"
    decision_path = root / "experiments" / DECISION
    validate_outputs([native_path, decision_path], [target_path, source_path], False)
    if sha256_file(target_path) != registration["edited_artifact_sha256"]:
        raise ValueError("Registered target changed")
    target = decode_artifact(load_artifact(target_path))
    source = decode_artifact(load_artifact(source_path))
    actual, capture_hash = None, None
    if capture.exists() and artifact_path.exists():
        artifact = load_artifact(artifact_path)
        capture_hash = sha256_file(capture)
        if artifact.metadata["source_sha256"] != capture_hash:
            raise ValueError("Analysis artifact is not from capture.wav")
        actual = decode_artifact(artifact)
    outcome, summary = classify(actual, target, source)
    native = {
        "analysis_version": "sample-memory-native-check-0.4",
        "hardware_verified": False,
        "outcome": outcome,
        "summary": summary,
        "capture_is_new": capture_hash is not None
        and capture_hash
        not in {registration["source_capture_sha256"], registration["restore_wav_sha256"]},
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": capture_hash,
        "artifact_sha256": sha256_file(artifact_path) if actual is not None else None,
        "native_frame": frame_report(actual) if actual is not None else None,
    }
    write_bytes(native_path, json_bytes(native))
    decision = {
        "analysis_version": "sample-memory-decision-0.4",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": sha256_file(native_path),
        "outcome": outcome,
        "hypothesis_supported": "accepted"
        if outcome == "accepted_exact"
        else ("advertised_limit_rejects" if outcome != "not_decoded" else None),
        "limits": registration["limits"],
    }
    if outcome == "accepted_exact" and playback.exists():
        pitch_path = folder / "key-frequency-results-001.json"
        validate_outputs([pitch_path], [playback], False)
        info, steps = step_frequencies(playback, SETTINGS)
        table = intervals(steps)
        write_bytes(
            pitch_path,
            json_bytes(
                {
                    "analysis_version": "sample-memory-frequencies-0.4",
                    "hardware_verified": False,
                    "playback_sha256": sha256_file(playback),
                    "settings": SETTINGS,
                    **info,
                    "step_frequencies_hz": {str(k): v for k, v in steps.items()},
                    "intervals": None
                    if table is None
                    else {
                        "step1_hz": table["step1_hz"],
                        "steps": {str(k): v for k, v in table["steps"].items()},
                    },
                }
            ),
        )
        decision.update(
            frequency_results_sha256=sha256_file(pitch_path),
            step1_hz=None if table is None else table["step1_hz"],
            measured_cents=None
            if table is None
            else {str(k): v["median_cents"] for k, v in table["steps"].items()},
            **decide(table, MODELS, SETTINGS),
            absolute=absolute_decision(None if table is None else table["step1_hz"]),
        )
    write_bytes(decision_path, json_bytes(decision))
    printed = {k: v for k, v in decision.items() if k not in ("limits", "registration_sha256")}
    print(json.dumps({**printed, "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
