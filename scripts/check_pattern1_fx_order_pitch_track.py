"""Check the fresh F6/6F pair: exact reception per leg, then the frozen step-1 decision.

Run with no arguments after both harness sessions. Writes each leg's native result,
each leg's pitch track, and the pair decision, all once.
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_fx_step_pitch_method import SETTINGS, decide, leg_step1, pitch_track
from scripts.prepare_pattern1_fx_order_pitch_track import REGISTRATION
from scripts.prepare_pattern1_fx_order_single_tone import leg_checks

DECISION = "pattern1-single-tone-FX-order-pitch-track-decision-001.json"


def native_check(root, registration, leg):
    spec = registration["legs"][leg]
    folder = root / "experiments" / spec["directory"]
    output = folder / "hardware-recapture-results-001.json"
    capture = folder / "capture.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    source_path = root / registration["source_artifact"]
    validate_outputs([output], [capture, artifact_path, target_path, source_path], False)
    if sha256_file(target_path) != spec["edited_artifact_sha256"]:
        raise ValueError(f"Leg {leg}: registered target changed")
    if sha256_file(source_path) != registration["source_artifact_sha256"]:
        raise ValueError("Registered source changed")
    artifact = load_artifact(artifact_path)
    capture_hash = sha256_file(capture)
    if artifact.metadata["source_sha256"] != capture_hash:
        raise ValueError(f"Leg {leg}: analysis artifact is not from capture.wav")
    base = decode_artifact(load_artifact(source_path))
    target = decode_artifact(load_artifact(target_path))
    actual = decode_artifact(artifact)
    checks = dict(
        leg_checks(base, actual, int(spec["footer_byte0"], 16)),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == spec["expected_body_sha256"],
        entire_actual_body_and_packets_match_target=actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        capture_is_new=capture_hash
        not in {registration["source_capture_sha256"], spec["restore_wav_sha256"]},
    )
    report = {
        "analysis_version": "single-tone-FX-order-pitch-track-leg-native-check-0.1",
        "hardware_verified": False,
        "leg": leg,
        "passed": all(checks.values()),
        "checks": checks,
        "registration_sha256": sha256_file(root / "experiments" / REGISTRATION),
        "capture_sha256": capture_hash,
        "artifact_sha256": sha256_file(artifact_path),
        "native_frame": frame_report(actual),
    }
    write_bytes(output, json_bytes(report))
    return report


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    method = root / "scripts/pattern1_fx_step_pitch_method.py"
    if sha256_file(method) != registration["method_script_sha256"]:
        raise ValueError("Frozen pitch method changed since registration")
    if registration["method_settings"] != SETTINGS:
        raise ValueError("Frozen pitch settings changed since registration")
    natives = {leg: native_check(root, registration, leg) for leg in ("a", "b")}
    if not all(report["passed"] for report in natives.values()):
        raise ValueError("Native reception failed; reports retained")
    folders = {leg: root / "experiments" / registration["legs"][leg]["directory"] for leg in "ab"}
    playbacks = {leg: folders[leg] / "playback.wav" for leg in "ab"}
    if sha256_file(playbacks["a"]) == sha256_file(playbacks["b"]):
        raise ValueError("Two independent playback recordings are required")
    outputs = {leg: folders[leg] / "pitch-track-results-001.json" for leg in "ab"}
    decision_path = root / "experiments" / DECISION
    validate_outputs([*outputs.values(), decision_path], list(playbacks.values()), False)
    reference = registration["reference_frequency_hz"]
    steps = {}
    for leg in "ab":
        track = pitch_track(playbacks[leg])
        steps[leg] = leg_step1(track, reference)
        write_bytes(
            outputs[leg],
            json_bytes(
                {
                    "analysis_version": "single-tone-FX-step1-pitch-track-0.1",
                    "hardware_verified": False,
                    "playback_sha256": sha256_file(playbacks[leg]),
                    "settings": SETTINGS,
                    "track": track,
                    "step1": steps[leg],
                }
            ),
        )
    decision = decide(steps["a"], steps["b"])
    result = {
        "analysis_version": "single-tone-FX-order-pitch-track-decision-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "native_results_sha256": {
            leg: sha256_file(folders[leg] / "hardware-recapture-results-001.json") for leg in "ab"
        },
        "pitch_results_sha256": {leg: sha256_file(path) for leg, path in outputs.items()},
        "step1": {leg: steps[leg]["median"] for leg in "ab"},
        "step1_loop_classes": {
            leg: [loop["class"] for loop in steps[leg]["loops"]] for leg in "ab"
        },
        **decision,
        "limits": registration["limits"],
    }
    write_bytes(decision_path, json_bytes(result))
    print(
        json.dumps(
            {
                "native": {leg: natives[leg]["passed"] for leg in "ab"},
                "step1": {leg: steps[leg]["median"]["class"] for leg in "ab"},
                "classification": result["classification"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
