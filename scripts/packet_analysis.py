"""Decode checksum-validated PO-33 packets without changing the phase source."""

import argparse
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--body-out", type=Path)
    args = p.parse_args()
    outputs = [args.out] + ([args.body_out] if args.body_out else [])
    validate_outputs(outputs, [args.artifact], False)
    artifact = load_artifact(args.artifact)
    frame = decode_artifact(artifact)
    if encode_packets(frame.packets) != frame.encoded_body:
        raise ValueError("Packet re-encoding does not match the captured encoded body")
    report = frame_report(frame)
    report.update(
        source_sha256=artifact.metadata["source_sha256"],
        artifact_sha256=sha256_file(args.artifact),
        exact_body_reencode=True,
    )
    if args.body_out:
        write_bytes(args.body_out, frame.encoded_body)
    write_bytes(args.out, json_bytes(report))


if __name__ == "__main__":
    main()
