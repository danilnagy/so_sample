"""Import an ordinary100ms48k stereo PCM WAV into a one-page Sound6 candidate."""

import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from po33_re.analysis.playback import measure_tone
from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.audio import load_pcm_wav
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    frame_report,
    rebuild_labels,
    sound_data,
    sound_groups,
)
from po33_re.formats.patterns import pattern_data
from po33_re.formats.samples import decode_signed_mulaw, encode_signed_mulaw, sound_at_48k
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data


def import_one_page_sound6(frame, native_audio):
    """Only the observed unshared nine-page Sound6 to this2344-code window."""
    if (
        not isinstance(native_audio, np.ndarray)
        or native_audio.ndim != 1
        or len(native_audio) != 2344
    ):
        raise ValueError("Exactly2344 mono native-rate floating-point samples required")
    quantized = encode_signed_mulaw(native_audio)
    groups = sound_groups(frame)
    data = sound_data(frame, 5)
    if len(data) != 36873 or data[:9].hex() != "00000000c078000005" or 6 not in groups or groups[6]:
        raise ValueError("Expected the observed nine-page Sound6 owner with empty Sound7")
    referrers = [
        key
        for key, indices in groups.items()
        if indices and len(record := sound_data(frame, key)) >= 9 and record[8] == 5
    ]
    if referrers != [5]:
        raise ValueError("Sound6 owner must be unshared")
    indices = groups[5]
    if (
        indices != list(range(indices[0], indices[-1] + 1))
        or [len(frame.packets[i].payload) for i in indices]
        != [255] * 16 + [25] + ([255] * 16 + [16]) * 8
    ):
        raise ValueError("Expected the observed nine-page packet geometry")
    codes = np.zeros(4096, dtype=np.uint8)
    codes[:2344] = quantized
    replacement = bytes(4) + (2344).to_bytes(4, "little") + b"\x05" + codes.tobytes()
    chunks = tuple(
        Packet(0xEF78, replacement[i : i + 255]) for i in range(0, len(replacement), 255)
    )
    return frame.packets[: indices[0]] + chunks + frame.packets[indices[-1] + 1 :]


def run(input_wav, directory):
    root = Path(__file__).resolve().parents[1]
    if directory.exists() or directory.is_symlink() or not directory.parent.is_dir():
        raise ValueError("Fresh output directory with existing parent required")
    input_hash, input_bytes = sha256_file(input_wav), input_wav.read_bytes()
    samples, info = load_pcm_wav(input_wav)
    if (
        info["sample_rate_hz"] != 48000
        or info["frames"] != 4800
        or not np.array_equal(samples[:, 0], samples[:, 1])
    ):
        raise ValueError("This probe requires100ms48k PCM with identical stereo channels")
    native_audio = resample_poly(samples[:, 0], 125, 256)
    baseline = root / "experiments/edited-sound6-nine-pages-001"
    acceptance_path = baseline / "hardware-acceptance-001.json"
    acceptance = json.loads(acceptance_path.read_text())
    source_path = baseline / "derived/analysis-001/capture.symbols.npz"
    if (
        not acceptance["hardware_verified"]
        or sha256_file(source_path) != acceptance["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != acceptance["capture_sha256"]
    ):
        raise ValueError("Matching verified nine-page source files required")
    source = load_artifact(source_path)
    source_bytes = source.to_bytes()
    original = decode_artifact(source)
    if hashlib.sha256(original.encoded_body).hexdigest() != acceptance["body_sha256"]:
        raise ValueError("Verified nine-page source body differs")
    edited = rebuild_labels(source, import_one_page_sound6(original, native_audio))
    edited.metadata["transformations"].append(
        {
            "kind": "ordinary-WAV-one-page-Sound6-import-probe",
            "input_wav_sha256": input_hash,
            "capacity_codes": 4096,
            "endpoint": 2344,
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    data = sound_data(target, 5)
    codes = np.frombuffer(data[9:], dtype=np.uint8)
    checks = {
        "imported_quantized_codes_match_saved_PCM_resampling": np.array_equal(
            codes[:2344], encode_signed_mulaw(native_audio)
        ),
        "zero_tail_codes": not np.any(codes[2344:]) and len(codes) == 4096,
        "one_page_geometry": [len(target.packets[i].payload) for i in sound_groups(target)[5]]
        == [255] * 16 + [25],
        "expected_header_and_frame_geometry": data[:9].hex() == "000000002809000005"
        and len(target.packets) == 832
        and target.end_byte == 160948,
        "all_non_sound6_plain_packets_preserved": excluding_destination_data(original, [5])
        == excluding_destination_data(target, [5]),
        "all_patterns_preserved": all(
            pattern_data(original, n) == pattern_data(target, n) for n in range(1, 17)
        ),
        "source_artifact_preserved": source.to_bytes() == source_bytes,
        "input_wav_unchanged": sha256_file(input_wav) == input_hash,
    }
    if not all(checks.values()):
        raise ValueError("One-page import locality or input checks failed")
    preview, preview_report = sound_at_48k(target, 6)
    fit = measure_tone(np.pad(preview, (0, 60000)), 48000)
    directory.mkdir()
    write_bytes(directory / "input-sample.wav", input_bytes)
    write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    restore = directory / "restore.wav"
    write_bytes(restore, waveform)
    buffer = io.BytesIO()
    sf.write(buffer, preview, 48000, format="WAV", subtype="FLOAT")
    write_bytes(directory / "sound6-preview.wav", buffer.getvalue())
    recovered = decode_wav(restore, 0.02)
    write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
    decoded = decode_artifact(recovered)
    comparison = compare_artifacts(edited, recovered)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        entire_target_body_after_wav_decode=decoded.encoded_body == target.encoded_body,
        entire_target_plain_packets_after_wav_decode=decoded.packets == target.packets,
        source_file_preserved=sha256_file(source_path) == acceptance["artifact_sha256"],
        copied_input_matches_original=sha256_file(directory / "input-sample.wav") == input_hash,
    )
    error = decode_signed_mulaw(codes[:2344]) - native_audio
    report = {
        "analysis_version": "ordinary-WAV-one-page-Sound6-import-0.1",
        "source_artifact": source_path.relative_to(root).as_posix(),
        "source_artifact_sha256": acceptance["artifact_sha256"],
        "source_capture_sha256": acceptance["capture_sha256"],
        "source_body_sha256": acceptance["body_sha256"],
        "source_acceptance_sha256": sha256_file(acceptance_path),
        "input_wav_sha256": input_hash,
        "input_audio": info,
        "input_channel_policy": "Require identical stereo and import left channel",
        "resampling_ratio": [125, 256],
        "sample_rate_hz_nominal": 23437.5,
        "imported_native_frames": 2344,
        "capacity_codes": 4096,
        "zero_tail_codes": 1752,
        "quantization_error_rms": float(np.sqrt(np.mean(error**2))),
        "restore_wav_sha256": sha256_file(restore),
        "edited_artifact_sha256": sha256_file(directory / "edited.symbols.npz"),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound6_header_hex": data[:9].hex(),
        "expected_sound6_payload_sha256": hashlib.sha256(data).hexdigest(),
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "target_frame": frame_report(target),
        "preview": preview_report,
        "independently_fitted_tone": fit,
        "tone_measurement_only_trailing_zero_frames": 60000,
        "hardware_verified": False,
        "public_writer_scope_changed": False,
        "limits": [
            "The actual saved PCM WAV is resampled and quantized without gain normalization; the pre-save sine is not used as a code oracle",
            "This probe tests one4096-code page and a new2344 endpoint under unshared Sound6; failure would not isolate size from endpoint interpretation by itself",
            "Ordinary WAV input is restricted to100ms48k identical stereo PCM for this calibration",
            "No arbitrary import, allocation or public copy/deletion scope is enabled before this hardware test",
        ],
    }
    write_bytes(directory / "software-validation.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("One-page import waveform checks failed; outputs retained")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample_wav", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.sample_wav, args.out_dir)


if __name__ == "__main__":
    main()
