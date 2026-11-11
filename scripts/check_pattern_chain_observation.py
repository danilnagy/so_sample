"""Read how the PO-33 stored a pattern chain, and which order it played."""

import argparse
import json
import math
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.hardware.changes import describe_changes
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_key_scale_grid_method import step_frequencies
from scripts.prepare_pattern_chain_observation import DIRECTORY, MODELS, REGISTRATION, SETTINGS

RESULT = "pattern-chain-result-001.json"


def global_byte_changes(baseline, actual):
    """Return {record ordinal: [(offset, before, after)]} for the 0x7d5c records."""
    before = [p.payload for p in baseline.packets if p.tag == 0x7D5C]
    after = [p.payload for p in actual.packets if p.tag == 0x7D5C]
    changes = {}
    for ordinal, (old, new) in enumerate(zip(before, after, strict=True)):
        diff = [(i, old[i], new[i]) for i in range(min(len(old), len(new))) if old[i] != new[i]]
        if diff or len(old) != len(new):
            changes[ordinal] = diff
    return changes


def only_globals_changed(baseline, actual):
    strip = [p for p in baseline.packets if p.tag != 0x7D5C]
    return strip == [p for p in actual.packets if p.tag != 0x7D5C]


def loop_matches(steps, expected_by_loop, tolerance):
    """Per loop: True when all 16 steps are within tolerance of that loop's frequencies."""
    matches = []
    for loop, expected in enumerate(expected_by_loop):
        ok = True
        for step in range(1, 17):
            values = steps.get(step, [])
            value = values[loop] if loop < len(values) else None
            if value is None or abs(1200 * math.log2(value / expected[step - 1])) > tolerance:
                ok = False
                break
        matches.append(ok)
    return matches


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / "scripts/pattern1_key_scale_grid_method.py")
        != registration["method_script_sha256"]
        or registration["method_settings"] != SETTINGS
        or registration["models_hz_by_loop"] != MODELS
    ):
        raise ValueError("Frozen method or models changed since registration")
    folder = root / "experiments" / DIRECTORY
    capture, playback = folder / "capture.wav", folder / "playback.wav"
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
    changes = global_byte_changes(baseline, actual)
    playback_result = None
    if playback.exists():
        info, steps = step_frequencies(playback, SETTINGS)
        matches = {
            name: loop_matches(steps, expected, SETTINGS["cents_tolerance"])
            for name, expected in MODELS.items()
        }
        holds = {name: sum(m) >= 4 for name, m in matches.items()}
        supported = [name for name, ok in holds.items() if ok]
        playback_result = {
            "playback_sha256": sha256_file(playback),
            **info,
            "step_frequencies_hz": {str(k): v for k, v in steps.items()},
            "loop_matches": matches,
            "model_support": holds,
            "classification": supported[0] if len(supported) == 1 else "other_or_inconclusive",
        }
    result = {
        "analysis_version": "pattern-chain-result-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "chain_in_global_record_only": only_globals_changed(baseline, actual),
        "global_byte_changes": {str(k): v for k, v in changes.items()},
        "all_changes": describe_changes(baseline, actual),
        "playback": playback_result,
    }
    write_bytes(output, json_bytes(result))
    print(
        json.dumps(
            {
                "chain_in_global_record_only": result["chain_in_global_record_only"],
                "global_byte_changes": result["global_byte_changes"],
                "playback": None
                if playback_result is None
                else {
                    "loop_matches": playback_result["loop_matches"],
                    "classification": playback_result["classification"],
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
