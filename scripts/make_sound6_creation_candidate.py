"""Prepare an isolated empty Sound6 creation test using observed Sound4 geometry."""

import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.analysis.playback import measure_tone
from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    encode_packets,
    frame_report,
    rebuild_labels,
    sound_data,
    sound_groups,
)
from po33_re.formats.patterns import pattern_data
from po33_re.formats.samples import encode_signed_mulaw, sound_at_48k
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data


def create_empty_owner_from_sound4_template(frame, template, sound_slot, codes):
    """Only Sound4 reconstruction or this Sound6 probe, using32768-code geometry.

    Sound4 permits an independent reconstruction of the real empty-to-recorded
    control. Sound6 is the next unverified candidate. No public allocator is added.
    """
    if type(sound_slot) is not int or sound_slot not in (4, 6):
        raise ValueError("Only Sound4 reconstruction and the Sound6 candidate are supported")
    if (
        not isinstance(codes, np.ndarray)
        or codes.dtype != np.uint8
        or codes.ndim != 1
        or len(codes) != 32768
    ):
        raise ValueError("Exactly32768 one-dimensional uint8 replacement codes required")
    selector = sound_slot - 1
    groups = sound_groups(frame)
    if selector not in groups or groups[selector]:
        raise ValueError("Existing destination selector must have no sample data")
    total_capacity = 0
    for key, indices in groups.items():
        if not indices:
            continue
        record = sound_data(frame, key)
        if len(record) < 9 or record[8] == selector:
            raise ValueError("Malformed sample or a reference to the empty destination owner")
        if len(record) > 9:
            if record[8] != key:
                raise ValueError("Existing full buffers must be self-owned")
            total_capacity += len(record) - 9
    # A bound on this probe, not a hardware memory-limit claim.
    if total_capacity + 32768 > 172032:
        raise ValueError("Probe would exceed the already observed total backing capacity")
    data = sound_data(template, 3)
    if len(data) != 32777 or data[:9].hex() not in ("00000000c06f000003", "00000000c078000003"):
        raise ValueError("Expected one of the observed self-owned Sound4 small layouts")
    template_indices = sound_groups(template)[3]
    lengths = [len(template.packets[i].payload) for i in template_indices]
    if (
        template_indices != list(range(template_indices[0], template_indices[-1] + 1))
        or lengths != [255] * 16 + [25] + ([255] * 16 + [16]) * 7
    ):
        raise ValueError("Expected contiguous observed4096-code page geometry")
    if excluding_destination_data(frame, [selector]) != excluding_destination_data(
        template, [selector]
    ):
        raise ValueError("Source and template must agree on every unrelated plain packet")
    replacement = data[:8] + bytes([selector]) + codes.tobytes()
    chunks, offset = [], 0
    for length in lengths:
        chunks.append(Packet(0xEF78, replacement[offset : offset + length]))
        offset += length
    if offset != len(replacement):
        raise ValueError("Template geometry does not cover the replacement")
    index = next(
        i for i, packet in enumerate(frame.packets) if packet == Packet(0x68B5, bytes([selector]))
    )
    return frame.packets[: index + 1] + tuple(chunks) + frame.packets[index + 1 :]


def run(directory):
    root = Path(__file__).resolve().parents[1]
    if directory.exists() or directory.is_symlink() or not directory.parent.is_dir():
        raise ValueError("Fresh output directory with an existing parent required")
    baseline = root / "experiments/edited-sound4-shrink-001"
    evidence_path = baseline / "hardware-acceptance-001.json"
    evidence = json.loads(evidence_path.read_text())
    source_path = baseline / "derived/analysis-001/capture.symbols.npz"
    if (
        not evidence["hardware_verified"]
        or sha256_file(source_path) != evidence["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != evidence["capture_sha256"]
    ):
        raise ValueError("Verified generated shrink and its unchanged source files required")
    source = load_artifact(source_path)
    original = decode_artifact(source)
    original_bytes = source.to_bytes()
    if hashlib.sha256(original.encoded_body).hexdigest() != evidence["body_sha256"]:
        raise ValueError("Verified source body differs")
    # Independently reconstruct the actual first empty-to-recorded Sound4 control.
    old_base = decode_artifact(
        load_artifact(
            root
            / "experiments/event-021-b-drum10-step9-key2/derived/analysis-001/capture.symbols.npz"
        )
    )
    old_recorded = decode_artifact(
        load_artifact(
            root
            / "experiments/event-022-b-record-independent-sound4/derived/analysis-001/capture.symbols.npz"
        )
    )
    reconstruction = encode_packets(
        create_empty_owner_from_sound4_template(
            old_base,
            old_recorded,
            4,
            np.frombuffer(sound_data(old_recorded, 3)[9:], dtype=np.uint8),
        )
    )
    if reconstruction != old_recorded.encoded_body:
        raise ValueError("Independent physical allocation reconstruction differs")
    capacity, endpoint, rate, frequency = 32768, 30912, 23437.5, 500
    tone = 0.25 * np.sin(2 * np.pi * frequency * np.arange(endpoint) / rate)
    fade = np.linspace(0, 1, 117)
    tone[:117] *= fade
    tone[-117:] *= fade[::-1]
    codes = np.zeros(capacity, dtype=np.uint8)
    codes[:endpoint] = encode_signed_mulaw(tone)
    edited = rebuild_labels(
        source, create_empty_owner_from_sound4_template(original, original, 6, codes)
    )
    edited.metadata["transformations"].append(
        {
            "kind": "empty-sound6-self-owner-creation-probe",
            "sound_slot": 6,
            "source_artifact_sha256": evidence["artifact_sha256"],
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    checks = {
        "independent_real_sound4_creation_reconstruction_exact": reconstruction
        == old_recorded.encoded_body,
        "destination_was_empty": sound_groups(original)[5] == [],
        "all_non_sound6_plain_packets_preserved": excluding_destination_data(original, [5])
        == excluding_destination_data(target, [5]),
        "all_patterns_preserved": all(
            pattern_data(original, n) == pattern_data(target, n) for n in range(1, 17)
        ),
        "new_sound6_self_owned_codes_match": sound_data(target, 5)
        == bytes.fromhex("00000000c078000005") + codes.tobytes(),
        "source_artifact_preserved": source.to_bytes() == original_bytes,
        "removing_only_inserted_packets_recovers_source": encode_packets(
            excluding_destination_data(target, [5])
        )
        == original.encoded_body,
        "expected_geometry": len(target.packets) == 951 and target.end_byte == 190215,
    }
    if not all(checks.values()):
        raise ValueError("Creation locality or geometry checks failed")
    preview, preview_report = sound_at_48k(target, 6)
    fit = measure_tone(np.pad(preview, (0, 60000)), 48000)
    directory.mkdir()
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
        generated_tone_fit=499 < fit["dominant_frequency_hz"] < 501,
        source_file_preserved=sha256_file(source_path) == evidence["artifact_sha256"],
    )
    report = {
        "analysis_version": "empty-sound6-creation-probe-0.1",
        "source_artifact": source_path.relative_to(root).as_posix(),
        "source_artifact_sha256": evidence["artifact_sha256"],
        "source_capture_sha256": evidence["capture_sha256"],
        "source_body_sha256": evidence["body_sha256"],
        "source_acceptance_sha256": sha256_file(evidence_path),
        "restore_wav_sha256": sha256_file(restore),
        "edited_artifact_sha256": sha256_file(directory / "edited.symbols.npz"),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound6_payload_sha256": hashlib.sha256(sound_data(target, 5)).hexdigest(),
        "expected_sound6_header_hex": sound_data(target, 5)[:9].hex(),
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "target_frame": frame_report(target),
        "preview": preview_report,
        "independently_fitted_tone": fit,
        "tone_measurement_only_trailing_zero_frames": 60000,
        "generated_frequency_hz": frequency,
        "nominal_tone_duration_seconds": endpoint / rate,
        "backing_capacity_before": 131072,
        "backing_capacity_after": 163840,
        "hardware_verified": False,
        "public_writer_scope_changed": False,
        "limits": [
            "One empty melodic Sound6 selector gets a self-owned32768-code sample using observed Sound4 headers and page geometry",
            "The final total backing capacity stays below an independently observed172032-code state; this is a probe bound, not a device memory-limit claim",
            "Allocation rounding, arbitrary slots/capacities, deletion and shared-owner mutation remain unsupported",
            "Exact native recapture and user audition checks are needed before hardware acceptance",
        ],
    }
    write_bytes(directory / "software-validation.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Creation waveform checks failed; outputs retained")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.out_dir)


if __name__ == "__main__":
    main()
