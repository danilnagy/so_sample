"""Check the registered single-tone F6/6F effect-order pair.

--leg a | --leg b  exact native reception of one leg (after its harness session)
--audio            both legs' first tones under the unchanged frozen method, the A/B
                   ratio decision and the registered reference cross-check
"""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.pattern1_fx_nibble_audio import PARAMETERS, audio_report, compare_audio
from scripts.prepare_pattern1_fx_order_single_tone import LEGS, REGISTRATION, leg_checks

COMPARISON = "pattern1-single-tone-FX-order-comparison-001.json"


def first_tones(report):
    return [
        m["fit"]["frequency_hz"] if m["usable"] and m["fit"] else None
        for channel in ("left", "right")
        for m in report["channels"][channel]["measurements"]
    ]


def reference_check(tones, expected_hz, tolerance):
    return len(tones) == 6 and all(
        tone is not None and abs(tone / expected_hz - 1) <= tolerance for tone in tones
    )


def classify(comparison, a_report, b_report, registration):
    """Combine the frozen ratio decision with the registered reference cross-check."""
    tolerance = registration["reference_relative_tolerance"]
    a_tones, b_tones = first_tones(a_report), first_tones(b_report)
    secondary = {}
    for model, prediction in registration["predictions"].items():
        secondary[model] = reference_check(
            a_tones, prediction["a_frequency_hz"], tolerance
        ) and reference_check(b_tones, prediction["b_frequency_hz"], tolerance)
    primary = comparison["classification"]
    supported = primary if secondary.get(primary) else None
    return {
        "primary_ratio_classification": primary,
        "reference_cross_check": secondary,
        "a_first_tones_hz": a_tones,
        "b_first_tones_hz": b_tones,
        "supported_model": supported,
        "classification": supported or "inconclusive",
    }


def check_leg(root, registration, leg):
    spec = registration["legs"][leg]
    folder = root / "experiments" / spec["directory"]
    output = folder / "hardware-recapture-results-001.json"
    capture = folder / "capture.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    source_path = root / registration["source_artifact"]
    validate_outputs([output], [capture, artifact_path, target_path, source_path], False)
    if sha256_file(target_path) != spec["edited_artifact_sha256"]:
        raise ValueError("Registered target artifact changed")
    if sha256_file(source_path) != registration["source_artifact_sha256"]:
        raise ValueError("Registered source artifact changed")
    artifact = load_artifact(artifact_path)
    capture_hash = sha256_file(capture)
    if artifact.metadata["source_sha256"] != capture_hash:
        raise ValueError("Analysis artifact does not come from capture.wav")
    base = decode_artifact(load_artifact(source_path))
    target = decode_artifact(load_artifact(target_path))
    actual = decode_artifact(artifact)
    footer = int(spec["footer_byte0"], 16)
    checks = dict(
        leg_checks(base, actual, footer),
        target_body_matches_registration=hashlib.sha256(target.encoded_body).hexdigest()
        == spec["expected_body_sha256"],
        entire_actual_body_and_packets_match_target=actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        capture_is_new=capture_hash
        not in {registration["source_capture_sha256"], spec["restore_wav_sha256"]},
    )
    report = {
        "analysis_version": "single-tone-FX-order-leg-native-check-0.1",
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
    if not report["passed"]:
        raise ValueError(f"Leg {leg} native check failed; report retained")
    return report


def check_audio(root, registration):
    folders = {leg: root / "experiments" / registration["legs"][leg]["directory"] for leg in "ab"}
    playbacks = {leg: folder / "playback.wav" for leg, folder in folders.items()}
    outputs = [folder / "first-tone-results-001.json" for folder in folders.values()]
    comparison_path = root / "experiments" / COMPARISON
    validate_outputs([*outputs, comparison_path], list(playbacks.values()), False)
    for leg, folder in folders.items():
        native = json.loads((folder / "hardware-recapture-results-001.json").read_text())
        if not native["passed"] or native["capture_sha256"] != sha256_file(folder / "capture.wav"):
            raise ValueError(f"Leg {leg} needs a passing native check first")
    if sha256_file(playbacks["a"]) == sha256_file(playbacks["b"]):
        raise ValueError("Two independent playback recordings are required")
    if registration["audio_parameters"] != PARAMETERS:
        raise ValueError("Frozen audio parameters changed since registration")
    for name, key in (
        ("scripts/pattern1_fx_nibble_audio.py", "audio_method_script_sha256"),
        ("scripts/sound3_pitch_frequency_analysis.py", "frequency_fit_helper_sha256"),
    ):
        if sha256_file(root / name) != registration[key]:
            raise ValueError(f"{name} changed since registration")
    reports = {leg: audio_report(playbacks[leg], PARAMETERS) for leg in "ab"}
    for output, leg in zip(outputs, "ab"):
        write_bytes(output, json_bytes(reports[leg]))
    comparison = compare_audio(reports["a"], reports["b"], PARAMETERS)
    result = dict(comparison, **classify(comparison, reports["a"], reports["b"], registration))
    result.update(
        analysis_version="single-tone-FX-order-comparison-0.1",
        registration_sha256=sha256_file(root / "experiments" / REGISTRATION),
        audio_results_sha256=[sha256_file(path) for path in outputs],
        playback_sha256={leg: sha256_file(path) for leg, path in playbacks.items()},
        hardware_verified=False,
        limits=registration["limits"],
    )
    write_bytes(comparison_path, json_bytes(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--leg", choices=("a", "b"))
    group.add_argument("--audio", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    registration = json.loads((root / "experiments" / REGISTRATION).read_text())
    if set(registration["legs"]) != set(LEGS):
        raise ValueError("Registration legs differ from the script")
    if args.leg:
        report = check_leg(root, registration, args.leg)
        print(json.dumps({"leg": args.leg, "passed": report["passed"]}))
    else:
        result = check_audio(root, registration)
        print(
            json.dumps(
                {
                    "classification": result["classification"],
                    "primary": result["primary_ratio_classification"],
                    "ratios": result["first_tone_ratios_A_over_B"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
