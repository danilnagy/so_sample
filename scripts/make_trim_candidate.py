"""Build a checksum-validated, zero-start melodic-reference trim experiment."""

import argparse
import hashlib
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import (
    decode_artifact,
    encode_packets,
    frame_report,
    rebuild_labels,
    replace_reference_counter,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact


def run(source_path, control_path, directory, counter):
    source, recorded_minimum = load_artifact(source_path), load_artifact(control_path)
    original, minimum = decode_artifact(source), decode_artifact(recorded_minimum)
    if encode_packets(replace_reference_counter(original, 3, 79)) != minimum.encoded_body:
        raise ValueError("Known minimum trim no longer reproduces the independent control")
    packets = replace_reference_counter(original, 3, counter)
    if len(packets) != len(original.packets):
        raise ValueError("Unexpected packet-count change")
    changes = [i for i, (a, b) in enumerate(zip(original.packets, packets)) if a != b]
    if len(changes) != 1:
        raise ValueError("Expected exactly one reference-packet change")
    paths = {
        name: directory / name
        for name in (
            "control.symbols.npz",
            "edited.symbols.npz",
            "control-restore.wav",
            "restore-sound3-short.wav",
            "control-redecoded.symbols.npz",
            "edited-redecoded.symbols.npz",
            "software-validation.json",
        )
    }
    validate_outputs(list(paths.values()), [source_path, control_path], False)
    details = {}
    for name, packet_set in (("control", original.packets), ("edited", packets)):
        artifact = rebuild_labels(source, packet_set)
        write_bytes(paths[name + ".symbols.npz"], artifact.to_bytes())
        waveform, encoding = encode_artifact(artifact, rate=44100, amplitude=0.5)
        wav_path = paths["control-restore.wav" if name == "control" else "restore-sound3-short.wav"]
        write_bytes(wav_path, waveform)
        decoded = decode_wav(wav_path, 0.02)
        write_bytes(paths[name + "-redecoded.symbols.npz"], decoded.to_bytes())
        comparison = compare_artifacts(artifact, decoded)
        decoded_frame = decode_artifact(decoded)
        if not comparison["passed"] or decoded_frame.packets != tuple(packet_set):
            raise ValueError("Rendered WAV does not preserve phase labels and packet contents")
        details[name] = {
            "wav_sha256": sha256_file(wav_path),
            "encoding": encoding,
            "strict_phase_roundtrip": comparison,
            "packets_after_wav_decode": frame_report(decoded_frame),
        }
    index = changes[0]
    report = {
        "analysis_version": "known-reference-trim-candidate-0.1",
        "source_artifact_sha256": sha256_file(source_path),
        "source_capture_sha256": source.metadata["source_sha256"],
        "independent_minimum_artifact_sha256": sha256_file(control_path),
        "known_minimum_body_reproduced": True,
        "changed_packet_index": index,
        "old_payload_hex": original.packets[index].payload.hex(),
        "new_payload_hex": packets[index].payload.hex(),
        "target_counter": counter,
        "edited_body_sha256": hashlib.sha256(encode_packets(packets)).hexdigest(),
        "packet_count_unchanged": True,
        "all_other_plain_packets_unchanged": True,
        "control_and_edited": details,
        "hardware_verified": False,
        "limits": [
            "Only the locally observed zero-start, shared melodic reference is supported.",
            "Length versus inclusive endpoint at nonzero start remains unverified.",
            "Source captures and partial ending intervals remain unchanged in their original artifacts.",
            "A new128-cell carrier follows the checksum-verified final packet; no raw capture is trimmed to encode it.",
            "Software validation does not establish hardware acceptance of this new candidate.",
        ],
    }
    write_bytes(paths["software-validation.json"], json_bytes(report))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("minimum_control", type=Path)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--counter", type=int, default=8000)
    args = p.parse_args()
    if args.out_dir.is_symlink():
        raise ValueError("Output directory cannot be a symbolic link")
    args.out_dir.mkdir(exist_ok=True)
    run(args.source, args.minimum_control, args.out_dir, args.counter)


if __name__ == "__main__":
    main()
