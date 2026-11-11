"""Expand the fixed Sound3 window using a calibrated experimental endpoint edit."""

import argparse
import hashlib
import io
import json
from pathlib import Path

import soundfile as sf
from scipy.signal import resample_poly

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import (
    decode_artifact,
    encode_packets,
    frame_report,
    rebuild_labels,
    replace_calibrated_reference_end,
    sound_data,
)
from po33_re.formats.patterns import pattern_data
from po33_re.formats.samples import extract_calibrated_window_sound
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact


def run(source_path, directory):
    root = Path(__file__).resolve().parents[1]
    validation_path = root / "experiments/sound3-start-min-results-001.json"
    observation_path = root / "experiments/event-013-b-sound3-start-min/audition-observation.json"
    validation = json.loads(validation_path.read_text())
    observation = json.loads(observation_path.read_text())
    if (
        not validation["control_passed"]
        or observation["user_answer"] != "Very short click or burst"
    ):
        raise ValueError("Minimum preservation and independent user audition are required")
    if sha256_file(source_path) != validation["artifact_sha256"]:
        raise ValueError("Source must match the reviewed fixed-start minimum capture")
    source = load_artifact(source_path)
    if source.metadata["source_sha256"] != observation["capture_sha256"]:
        raise ValueError("Audition observation must refer to the source capture")
    original = decode_artifact(source)
    unchanged = source.to_bytes()
    maximum_path = (
        root / "experiments/event-012-b-sound3-start/derived/analysis-001/capture.symbols.npz"
    )
    maximum = decode_artifact(load_artifact(maximum_path))
    if encode_packets(replace_calibrated_reference_end(original, 3, 65535)) != maximum.encoded_body:
        raise ValueError("Writer does not reproduce the genuine larger endpoint body")
    if encode_packets(replace_calibrated_reference_end(maximum, 3, 31504)) != original.encoded_body:
        raise ValueError("Writer does not reproduce the genuine minimum endpoint inverse")
    edited = rebuild_labels(source, replace_calibrated_reference_end(original, 3, 39393))
    edited.metadata["transformations"].append(
        {
            "kind": "calibrated-nonzero-reference-end-edit",
            "sound_slot": 3,
            "start_field": 31393,
            "endpoint_field": 39393,
            "source_artifact_sha256": sha256_file(source_path),
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    before, after = sound_data(original, 2), sound_data(target, 2)
    changes = [
        {"offset": i, "old": a, "new": b} for i, (a, b) in enumerate(zip(before, after)) if a != b
    ]
    packet_changes = [i for i, (a, b) in enumerate(zip(original.packets, target.packets)) if a != b]
    checks = {
        "genuine_forward_and_inverse_endpoint_bodies_reproduced": True,
        "only_expected_endpoint_bytes_changed": changes
        == [{"offset": 4, "old": 16, "new": 225}, {"offset": 5, "old": 123, "new": 153}],
        "only_sound3_reference_packet_changed": packet_changes == [375],
        "start_and_owner_preserved": before[:4] == after[:4] and before[8:] == after[8:],
        "backing_owner_preserved": sound_data(original, 0) == sound_data(target, 0),
        "all_patterns_preserved": all(
            pattern_data(original, p) == pattern_data(target, p) for p in range(1, 17)
        ),
        "source_artifact_preserved": source.to_bytes() == unchanged,
        "packet_count": len(original.packets) == len(target.packets) == 511,
        "packet_tags_and_lengths": all(
            a.tag == b.tag and len(a.payload) == len(b.payload)
            for a, b in zip(original.packets, target.packets)
        ),
        "candidate_inverse_reproduces_source": encode_packets(
            replace_calibrated_reference_end(target, 3, 31504)
        )
        == original.encoded_body,
    }
    samples, preview = extract_calibrated_window_sound(target, 3)
    buffer = io.BytesIO()
    resampled = resample_poly(samples, 256, 125)
    sf.write(buffer, resampled, 48000, format="WAV", subtype="FLOAT")
    names = [
        "edited.symbols.npz",
        "restore-sound3-window.wav",
        "redecoded.symbols.npz",
        "window-preview-48k.wav",
        "software-validation.json",
    ]
    paths = {name: directory / name for name in names}
    validate_outputs(
        list(paths.values()), [source_path, validation_path, observation_path, maximum_path], False
    )
    write_bytes(paths["edited.symbols.npz"], edited.to_bytes())
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    write_bytes(paths["restore-sound3-window.wav"], waveform)
    write_bytes(paths["window-preview-48k.wav"], buffer.getvalue())
    redecoded = decode_wav(paths["restore-sound3-window.wav"], 0.02)
    write_bytes(paths["redecoded.symbols.npz"], redecoded.to_bytes())
    comparison = compare_artifacts(edited, redecoded)
    recovered = decode_artifact(redecoded)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        exact_target_body_after_wav_decode=recovered.encoded_body == target.encoded_body,
        exact_target_packets_after_wav_decode=recovered.packets == target.packets,
        preview_code_count=len(samples) == 8000,
        preview_frame_count=len(resampled) == 16384,
    )
    report = {
        "analysis_version": "calibrated-nonzero-trim-candidate-0.1",
        "source_capture_sha256": source.metadata["source_sha256"],
        "source_artifact_sha256": sha256_file(source_path),
        "restore_wav_sha256": sha256_file(paths["restore-sound3-window.wav"]),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound3_header_hex": after.hex(),
        "start_field": 31393,
        "endpoint_field": 39393,
        "sound3_reference_byte_changes": changes,
        "changed_plain_packet_indices": packet_changes,
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "packets_after_wav_decode": frame_report(recovered),
        "preview": {
            **preview,
            "export_sample_rate_hz": 48000,
            "export_frames": len(resampled),
            "nominal_duration_seconds": len(samples) / 23437.5,
        },
        "hardware_verified": False,
        "limits": [
            "Only fixed Sound3 start31393 with owner0 and the observed31504..65535 endpoint interval is supported",
            "The endpoint interpretation is locally supported by physical changes and the reported minimum burst; this generated edit needs its own hardware test",
            "Preview uses explicit half-open[start,end); hardware endpoint inclusivity and a general minimum rule remain unresolved",
            "The failed exact minimum predictions remain retained; no resizing, allocation, other starts or sound slots are enabled",
        ],
    }
    write_bytes(paths["software-validation.json"], json_bytes(report))
    if not report["passed"]:
        raise ValueError("Nonzero trim candidate software checks failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.out_dir.is_symlink():
        raise ValueError("Output directory cannot be a symbolic link")
    args.out_dir.mkdir(exist_ok=True)
    run(args.source, args.out_dir)


if __name__ == "__main__":
    main()
