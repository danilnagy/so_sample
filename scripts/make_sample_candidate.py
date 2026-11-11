"""Replace the retained backing buffer with a generated750Hz calibration tone."""

import argparse
import hashlib
import io
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.audio import load_pcm_wav
from po33_re.formats.packets import (
    decode_artifact,
    decode_frame,
    encode_packets,
    frame_report,
    rebuild_labels,
    sound_data,
    sound_groups,
)
from po33_re.formats.samples import decode_signed_mulaw, encode_signed_mulaw, replace_owner_codes
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact


def pcm_wav(samples, rate):
    output = io.BytesIO()
    sf.write(output, np.column_stack((samples, samples)), rate, format="WAV", subtype="PCM_16")
    return output.getvalue()


def run(source_path, directory):
    source = load_artifact(source_path)
    original = decode_artifact(source)
    source_bytes = source.to_bytes()
    owner = sound_data(original, 0)
    expected_headers = {
        0: "00000000c0fc000000",
        1: "00000000c0fc000000",
        2: "00000000401f000000",
        7: "00000000c0fc000000",
    }
    if any(sound_data(original, i)[:9].hex() != h for i, h in expected_headers.items()):
        raise ValueError("Source does not match the hardware-validated trim state")
    if len(owner) != 65545:
        raise ValueError("Expected the existing65536-byte owner buffer")
    paths = {
        name: directory / name
        for name in (
            "sample-750hz.wav",
            "imported-preview.wav",
            "edited.symbols.npz",
            "restore-750hz.wav",
            "redecoded.symbols.npz",
            "software-validation.json",
        )
    }
    validate_outputs(list(paths.values()), [source_path], False)
    # Two seconds at48k, with5ms fades, peak0.25; no automatic playback.
    tone = 0.25 * np.sin(2 * np.pi * 750 * np.arange(96000) / 48000)
    fade = np.linspace(0, 1, 240)
    tone[:240] *= fade
    tone[-240:] *= fade[::-1]
    write_bytes(paths["sample-750hz.wav"], pcm_wav(tone, 48000))
    samples, info = load_pcm_wav(paths["sample-750hz.wav"])
    if info["sample_rate_hz"] != 48000 or not np.array_equal(samples[:, 0], samples[:, 1]):
        raise ValueError("Calibration source must be identical stereo48k PCM")
    # Import the actual saved PCM file, rather than the pre-quantization sine.
    native_audio = resample_poly(samples[:, 0], 125, 256)
    codes = np.zeros(len(owner) - 9, dtype=np.uint8)
    if len(native_audio) > len(codes):
        raise ValueError("Calibration audio exceeds the existing backing buffer")
    codes[: len(native_audio)] = encode_signed_mulaw(native_audio)
    packets = replace_owner_codes(original, 1, codes)
    changed = [i for i, (a, b) in enumerate(zip(original.packets, packets)) if a != b]
    allowed = set(sound_groups(original)[0])
    target_body = encode_packets(packets)
    target = decode_frame(target_body, start=0)
    checks = {
        "only_owner_data_packets_changed": bool(changed) and set(changed) <= allowed,
        "packet_tags_and_lengths_unchanged": all(
            a.tag == b.tag and len(a.payload) == len(b.payload)
            for a, b in zip(original.packets, packets)
        ),
        "packet_count_unchanged": len(original.packets) == len(packets) == 511,
        "all_sound_headers_unchanged": all(
            sound_data(target, i)[:9] == sound_data(original, i)[:9] for i in expected_headers
        ),
        "backing_codes_exact": sound_data(target, 0)[9:] == codes.tobytes(),
        "source_artifact_preserved": source.to_bytes() == source_bytes,
    }
    decoded_audio = decode_signed_mulaw(codes)
    preview = resample_poly(decoded_audio, 256, 125)
    write_bytes(paths["imported-preview.wav"], pcm_wav(preview, 48000))
    artifact = rebuild_labels(source, packets)
    write_bytes(paths["edited.symbols.npz"], artifact.to_bytes())
    waveform, encoding = encode_artifact(artifact, rate=44100, amplitude=0.5)
    write_bytes(paths["restore-750hz.wav"], waveform)
    redecoded = decode_wav(paths["restore-750hz.wav"], 0.02)
    write_bytes(paths["redecoded.symbols.npz"], redecoded.to_bytes())
    comparison = compare_artifacts(artifact, redecoded)
    recovered = decode_artifact(redecoded)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        exact_target_packets_after_wav_decode=recovered.packets == packets,
        exact_target_body_after_wav_decode=recovered.encoded_body == target_body,
    )
    error = decoded_audio[: len(native_audio)] - native_audio
    report = {
        "analysis_version": "fixed-buffer-sample-candidate-0.1",
        "source_artifact_sha256": sha256_file(source_path),
        "source_capture_sha256": source.metadata["source_sha256"],
        "source_pcm_sha256": sha256_file(paths["sample-750hz.wav"]),
        "restore_wav_sha256": sha256_file(paths["restore-750hz.wav"]),
        "expected_body_sha256": hashlib.sha256(target_body).hexdigest(),
        "backing_codes_sha256": hashlib.sha256(codes.tobytes()).hexdigest(),
        "input_frames_at_nominal23437_5hz": len(native_audio),
        "zero_padding_samples": len(codes) - len(native_audio),
        "input_peak": float(abs(native_audio).max()),
        "quantization_error_rms": float(np.sqrt(np.mean(error**2))),
        "quantization_snr_db": float(10 * np.log10(np.mean(native_audio**2) / np.mean(error**2))),
        "changed_packet_indices": changed,
        "affected_sound_slots": [1, 2, 3, 8],
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "packets_after_wav_decode": frame_report(recovered),
        "hardware_verified": False,
        "limits": [
            "This is an experimental fixed-size replacement, not sample allocation or resizing.",
            "Sounds1/2/3/8 share the owner and all receive the new tone; existing trim counters are preserved.",
            "Sound3 remains short; other copies have two seconds of nominal750Hz audio and quiet padding.",
            "The sample codec encoder still needs this separate hardware test.",
        ],
    }
    write_bytes(paths["software-validation.json"], json_bytes(report))
    if not report["passed"]:
        raise ValueError("Sample candidate validation failed")


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
