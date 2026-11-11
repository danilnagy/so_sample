"""Register fixed B32 at LPF16 and an interior amplitude hypothesis before new data."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact, frame_report, rebuild_labels
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_filter_probe import recorded_report

MAXIMUM_BODY = "fd0817c1c7791225eab3fe2f2d91f459ddad0c00fd0aacbd87e8672232323039"
DIRECTORY = "edited-sound3-filter16-B32-middle-001"
REGISTRATION = "sound3-generated-filter16-B32-middle-registration-001.json"


def fixed_middle_packets(frame, value=32):
    if hashlib.sha256(frame.encoded_body).hexdigest() != MAXIMUM_BODY:
        raise ValueError("Exact accepted LPF16/B63 source required")
    if type(value) is not int or value != 32:
        raise ValueError("Only fixed research B32 allowed")
    data = bytearray(pattern_data(frame, 1))
    for step in range(16):
        data[48 * step + 8] = (data[48 * step + 8] & 3) | 128
    return _replace_pattern_data(frame, 1, bytes(data))


def middle_preservation_checks(base, actual, registration):
    context = recorded_report(base, actual, registration)
    a, b = [bytearray(pattern_data(frame, 1)) for frame in (base, actual)]
    for data in (a, b):
        for step in range(16):
            data[48 * step + 8] &= 3
    fields = context["raw_Sound3_fields"]["after"]
    data = pattern_data(actual, 1)
    return dict(
        context["native_checks"],
        **context["preservation_checks"],
        source_is_exact_LPF16_B63=hashlib.sha256(base.encoded_body).hexdigest() == MAXIMUM_BODY,
        only_six_B_bits_changed=a == b,
        cutoff16_pitch14_volume36_preserved=fields["uninterpreted_candidate_values"] == [16] * 16
        and fields["first_low5_values"] == [14] * 16
        and fields["volume_values"] == [36] * 16,
        all16_B_values_are32=[data[48 * step + 8] >> 2 for step in range(16)] == [32] * 16,
    )


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if directory.exists() or directory.is_symlink() or registration_path.exists():
        raise ValueError("Fresh B32 registration and output folder required")
    pair_path = root / "experiments/sound3-generated-filter16-B0-B63-registration-001.json"
    pair = json.loads(pair_path.read_text())
    endpoints = []
    for leg in pair["expected_capture_sequence"]:
        folder = root / "experiments" / leg["experiment_id"]
        observation_path = folder / "hardware-observation-001.json"
        observation = json.loads(observation_path.read_text())
        native_path = folder / "hardware-recapture-results-001.json"
        audio_path = folder / "resonance-frequency-results-001.json"
        audio = json.loads(audio_path.read_text())
        if (
            not observation["hardware_verified"]
            or not all(observation["checks"].values())
            or not audio["passed"]
            or audio["parameters"] != pair["frequency_method"]["parameters"]
            or audio["source_sha256"] != sha256_file(folder / "playback.wav")
            or sha256_file(root / observation["artifact_path"]) != observation["artifact_sha256"]
            or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
            or sha256_file(audio_path) != observation["frequency_results_sha256"]
            or sha256_file(native_path) != observation["native_results_sha256"]
        ):
            raise ValueError("Verified frozen endpoint native and audio evidence required")
        endpoints.append(
            {
                "raw_B_value": leg["raw_B_value"],
                "audio_results": audio_path.relative_to(root).as_posix(),
                "audio_results_sha256": sha256_file(audio_path),
                "playback": (folder / "playback.wav").relative_to(root).as_posix(),
                "playback_sha256": sha256_file(folder / "playback.wav"),
                "native_results": native_path.relative_to(root).as_posix(),
                "native_results_sha256": sha256_file(native_path),
                "capture": (folder / "capture.wav").relative_to(root).as_posix(),
                "capture_sha256": observation["capture_sha256"],
                "artifact": observation["artifact_path"],
                "artifact_sha256": observation["artifact_sha256"],
                "observation": observation_path.relative_to(root).as_posix(),
                "observation_sha256": sha256_file(observation_path),
            }
        )
    source_path = root / endpoints[1]["artifact"]
    source = load_artifact(source_path)
    base = decode_artifact(source)
    unchanged = source.to_bytes()
    edited = rebuild_labels(source, fixed_middle_packets(base))
    edited.metadata["transformations"].append(
        {"kind": "research-fixed-LPF16-B32", "hardware_verified": False}
    )
    target = decode_artifact(edited)
    checks = middle_preservation_checks(base, target, pair)
    if not all(checks.values()):
        raise ValueError("B32 native preservation failed")
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    directory.mkdir()
    write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
    write_bytes(directory / "restore.wav", waveform)
    recovered = decode_wav(directory / "restore.wav", 0.02)
    write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
    actual = decode_artifact(recovered)
    comparison = compare_artifacts(edited, recovered)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        entire_target_body_and_packets_after_wav_decode=actual.encoded_body == target.encoded_body
        and actual.packets == target.packets,
        source_preserved=source.to_bytes() == unchanged
        and sha256_file(source_path) == endpoints[1]["artifact_sha256"],
    )
    write_bytes(
        directory / "software-validation.json",
        json_bytes(
            {
                "analysis_version": "fixed-B32-native-and-waveform-validation-0.1",
                "hardware_verified": False,
                "passed": all(checks.values()),
                "checks": checks,
                "encoding": encoding,
                "target_frame": frame_report(target),
                "strict_phase_roundtrip": comparison,
            }
        ),
    )
    if not all(checks.values()):
        raise ValueError("B32 waveform failed; outputs retained")
    limits = [
        "B32 target is new and has no physical recapture yet; endpoints were already observed before this new interior registration",
        "New hypothesis requires middle amplitude above minimum by at least5% and maximum above middle by at least5% in all six common measurements; failure remains retained",
        "Original common audio method, windows, thresholds, band and search remain unchanged; missing/quiet/distorted audio is not refitted",
        "Only fixed32 from exact accepted LPF16/B63 is allowed by constructor; no general resonance writer or cutoff guard extension",
        "Literal32 tests an interior code and bit7 with lower candidate bits clear; no numeric UI midpoint, proportional Q scale or complete bit7 semantics inferred",
    ]
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "generated-B32-interior-and-frozen-endpoint-comparison-preregistration-0.1",
                "hardware_verified": False,
                "registered_before_middle_native_and_audio": True,
                "endpoint_audio_already_observed": True,
                "experiment_id": DIRECTORY,
                "source_artifact": endpoints[1]["artifact"],
                "source_artifact_sha256": endpoints[1]["artifact_sha256"],
                "source_capture": endpoints[1]["capture"],
                "source_capture_sha256": endpoints[1]["capture_sha256"],
                "source_body_sha256": MAXIMUM_BODY,
                "source_observation_sha256": endpoints[1]["observation_sha256"],
                "candidate": pair["candidate"],
                "broader_FILTER_candidate": pair["broader_FILTER_candidate"],
                "expected_packet_count": 815,
                "expected_frame_end_byte": 156758,
                "expected_B_value": 32,
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "restore_wav_sha256": sha256_file(directory / "restore.wav"),
                "edited_artifact_sha256": sha256_file(directory / "edited.symbols.npz"),
                "software_validation_sha256": sha256_file(directory / "software-validation.json"),
                "endpoint_inputs": endpoints,
                "pair_registration_sha256": sha256_file(pair_path),
                "frequency_method": pair["frequency_method"],
                "resonance_comparison_parameters": pair["resonance_comparison_parameters"],
                "original_frequency_registration": pair["original_frequency_registration"],
                "original_frequency_registration_sha256": pair[
                    "original_frequency_registration_sha256"
                ],
                "hypothesis": "B32 repeated-component amplitude is between observed B0 and B63, with both adjacent amplitude ratios at least1.05 and consistent pitch/loop",
                "limits": limits,
            }
        ),
    )
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_generated_B32_middle_backup_and_audio",
                "restore_file": "restore.wav",
                "registration": "../" + REGISTRATION,
                "hardware_restore": {"status": "not_run"},
                "planned_actions": [
                    "Restore with established stereo setup and playback level; keep both knobs and recording settings unchanged",
                    "Before playback save full capture.wav at established reduced level with one second trailing silence",
                    "Select Pattern1/Sound3/FILTER without knob movement; separately record12 to15 seconds ordinary playback as playback.wav, then stop/write off",
                    "Report actual sound, including uncertainty; no WRITE-held pass or required guessed comparison",
                ],
            }
        ),
    )
    print(
        json.dumps(
            {
                "passed": True,
                "next_restore": DIRECTORY + "/restore.wav",
                "target_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
