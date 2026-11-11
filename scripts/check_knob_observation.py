"""Locate the bytes that turning Sound16's knobs without WRITE changed."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, sound_data, sound_groups
from po33_re.formats.patterns import pattern_data
from po33_re.hardware.changes import describe_changes
from po33_re.modem.symbols import load_artifact
from scripts.check_pattern_chain_observation import global_byte_changes
from scripts.prepare_knob_observation import DIRECTORY, REGISTRATION

RESULT = "sound-knobs-result-001.json"
KNOB_SOUND = 16


def record(frame, sid):
    return sound_data(frame, sid) if sound_groups(frame).get(sid) else b""


def cell_changes(baseline, actual):
    """Every changed pattern byte as (pattern, region, step, sound or None, offset, old, new)."""
    changes = []
    for pattern in range(1, 17):
        old, new = pattern_data(baseline, pattern), pattern_data(actual, pattern)
        for offset, (a, b) in enumerate(zip(old, new, strict=True)):
            if a == b:
                continue
            if offset < 768:
                step, sound = offset // 48 + 1, (offset % 48) // 3 + 1
                region = "primary"
            elif offset < 1024:
                step, sound = (offset - 768) // 16 + 1, (offset - 768) % 16 + 1
                region = "auxiliary"
            else:
                step, sound, region = None, None, "footer"
            changes.append([pattern, region, step, sound, offset, a, b])
    return changes


def classify(baseline, actual):
    globals_ = global_byte_changes(baseline, actual)
    cells = cell_changes(baseline, actual)
    sounds = sorted(
        sid
        for sid in set(sound_groups(baseline)) | set(sound_groups(actual))
        if record(baseline, sid) != record(actual, sid)
    )
    regions = {
        "global_records": bool(globals_),
        "pattern_cells": bool(cells),
        "sound_records": bool(sounds),
    }
    if not any(regions.values()):
        outcome = "nothing_stored"
    elif sum(regions.values()) > 1:
        outcome = "mixed"
    elif globals_:
        outcome = "global_records_only"
    elif sounds:
        outcome = "sound_records_only"
    elif all(c[3] == KNOB_SOUND for c in cells):
        outcome = "sound16_cells_only"
    else:
        outcome = "mixed"
    return outcome, {
        "global_byte_changes": {str(k): v for k, v in globals_.items()},
        "pattern_byte_changes": cells,
        "changed_sound_ids": sounds,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    folder = root / "experiments" / DIRECTORY
    capture = folder / "capture.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    baseline_path = root / registration["baseline_artifact"]
    output = root / "experiments" / RESULT
    validate_outputs([output], [capture, artifact_path, baseline_path], False)
    if sha256_file(baseline_path) != registration["baseline_artifact_sha256"]:
        raise ValueError("Baseline changed since registration")
    artifact = load_artifact(artifact_path)
    if artifact.metadata["source_sha256"] != sha256_file(capture):
        raise ValueError("Analysis artifact is not from capture.wav")
    baseline = decode_artifact(load_artifact(baseline_path))
    actual = decode_artifact(artifact)
    outcome, details = classify(baseline, actual)
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "sound-knobs-result-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": sha256_file(capture),
                "artifact_sha256": sha256_file(artifact_path),
                "outcome": outcome,
                **details,
                "all_changes": describe_changes(baseline, actual),
            }
        ),
    )
    print(json.dumps({"outcome": outcome, **details}))


if __name__ == "__main__":
    main()
