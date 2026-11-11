"""Read the effect code each FX key stored, against the registered key-minus-one model."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import pattern_data
from po33_re.hardware.changes import describe_changes
from po33_re.modem.symbols import load_artifact
from scripts.prepare_fx_code_map import DIRECTORY, REGISTRATION

RESULT = "FX-code-map-result-001.json"


def footer_codes(footer):
    """The 16 per-step nibbles, step 1 first (high nibble of byte 0)."""
    return [f"{nibble:X}" for byte in footer for nibble in (byte >> 4, byte & 15)]


def map_keys(frame, registration):
    keys = {}
    for key, pattern in registration["assignments"].items():
        steps = footer_codes(pattern_data(frame, pattern)[1024:])
        codes = sorted({c for c in steps if c != "F"})
        keys[key] = {
            "pattern": pattern,
            "steps": "".join(steps),
            "codes": codes,
            "steps_with_effect": sum(c != "F" for c in steps),
            "mapped_code": codes[0] if len(codes) == 1 else None,
            "matches_prediction": codes == [registration["predicted_codes"][key]],
        }
    return keys


def decide(keys, registration):
    controls = all(keys[k]["mapped_code"] == v for k, v in registration["known_controls"].items())
    supported = controls and all(item["matches_prediction"] for item in keys.values())
    return {
        "controls_match": controls,
        "key_minus_one_supported": supported,
        "classification": "key_minus_one" if supported else "not_supported_or_partial",
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
        raise ValueError("Baseline artifact changed since registration")
    artifact = load_artifact(artifact_path)
    if artifact.metadata["source_sha256"] != sha256_file(capture):
        raise ValueError("Analysis artifact is not from capture.wav")
    baseline = decode_artifact(load_artifact(baseline_path))
    frame = decode_artifact(artifact)
    keys = map_keys(frame, registration)
    changes = describe_changes(baseline, frame)
    footer_patterns = {item["pattern"] for item in keys.values()}
    other = [
        c
        for c in changes["changes"]
        if not (c["region"] == "pattern_footer" and c["pattern"] in footer_patterns)
    ]
    result = {
        "analysis_version": "FX-code-map-result-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": sha256_file(capture),
        "artifact_sha256": sha256_file(artifact_path),
        "keys": keys,
        **decide(keys, registration),
        "other_changes": other,
    }
    write_bytes(output, json_bytes(result))
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "map": {k: v["mapped_code"] for k, v in keys.items()},
                "steps": {k: v["steps"] for k, v in keys.items()},
                "other_change_count": len(other),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
