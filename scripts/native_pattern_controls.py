"""Retrospectively inspect native pattern payloads from the existing kick controls."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import Packet, decode_artifact, encode_packets
from po33_re.formats.patterns import pattern_data, pattern_groups, patterns_report
from po33_re.modem.symbols import load_artifact


def replace_pattern_bytes(frame, data):
    # An analysis-only opaque rewrite to compare known captures, not a note writer.
    packets, offset = list(frame.packets), 0
    for index in pattern_groups(frame)[0]:
        packet = packets[index]
        length = len(packet.payload)
        packets[index] = Packet(packet.tag, data[offset : offset + length])
        offset += length
    if offset != len(data):
        raise ValueError("Pattern chunks do not cover the comparison data")
    return tuple(packets)


def main():
    root = Path(__file__).resolve().parents[1]
    corpus_path = root / "experiments/packet-corpus-002.json"
    corpus = json.loads(corpus_path.read_text())
    manifest = json.loads((root / "tests/fixtures/manifest.json").read_text())
    registered = {e["path"]: e["sha256"] for e in manifest["captures"]}
    frames, records = {}, []
    for record in corpus["records"]:
        if not record.get("exact_body_reencode"):
            continue
        name = Path(record["source_capture"]).parent.name
        if not name.startswith("event-"):
            continue
        source = root / record["source_capture"]
        artifact_path = root / record["artifact"]
        artifact = load_artifact(artifact_path)
        source_hash = sha256_file(source)
        if (
            source_hash != registered[record["source_capture"]]
            or source_hash != artifact.metadata["source_sha256"]
        ):
            raise ValueError("Control artifact does not match the registered source WAV")
        frame = decode_artifact(artifact)
        frames[name] = frame
        records.append(
            {
                "experiment_id": name,
                "source_sha256": source_hash,
                "artifact_sha256": sha256_file(artifact_path),
                "packet_count": len(frame.packets),
                "pattern1": patterns_report(frame)["patterns"][0],
            }
        )
    base = frames["event-002-a"]
    empty = pattern_data(base, 1)
    first = pattern_data(frames["event-001-b"], 1)
    region, auxiliary = first[24:36], first[768:784]
    if region.hex() != "cff683000000000000000000" or not any(auxiliary):
        raise ValueError("Step1 control does not match the reviewed raw regions")
    reconstructions = []
    for name, steps in (
        ("event-002-b", [2]),
        ("event-003-b", [3]),
        ("event-005-b-joint", [1, 2]),
    ):
        predicted = bytearray(empty)
        for step in steps:
            offset = 48 * (step - 1) + 24
            predicted[offset : offset + 12] = region
            offset = 768 + 16 * (step - 1)
            predicted[offset : offset + 16] = auxiliary
        predicted = bytes(predicted)
        actual = pattern_data(frames[name], 1)
        differences = [
            {"offset": i, "predicted": a, "actual": b}
            for i, (a, b) in enumerate(zip(predicted, actual))
            if a != b
        ]
        packets = replace_pattern_bytes(base, predicted)
        reconstructions.append(
            {
                "target_experiment": name,
                "steps": steps,
                "pattern_data_matches": predicted == actual,
                "pattern_byte_differences": differences,
                "whole_plain_packet_list_matches": packets == frames[name].packets,
                "whole_encoded_body_matches": encode_packets(packets) == frames[name].encoded_body,
            }
        )
    current_path = root / "experiments/edited-sample-001/derived/analysis-001/capture.symbols.npz"
    current = decode_artifact(load_artifact(current_path))
    report = {
        "analysis_version": "native-pattern-control-analysis-0.1",
        "analysis_type": "Retrospective reconstruction after viewing the captures; not preregistered prediction",
        "controls": records,
        "step1_primary_region_hex": region.hex(),
        "step1_auxiliary_row_hex": auxiliary.hex(),
        "reconstructions_from_step1": reconstructions,
        "current_pattern1_equals_control_empty_bytes": pattern_data(current, 1) == empty,
        "empty_pattern1_sha256": hashlib.sha256(empty).hexdigest(),
        "limits": [
            "The Step2-only auxiliary byte792 is17, whereas the Step1-derived and joint value is16; its meaning is not known.",
            "The identical primary region and48-byte step stride are observed; general note field encoding is not inferred.",
            "Old phase-domain prediction failures are retained and are not retroactively counted as passes.",
            "The corrected joint analysis002 is used via the source-matched corpus; the wrong-upload artifact is excluded.",
        ],
    }
    output = root / "experiments/native-pattern-controls-001.json"
    validate_outputs([output], [corpus_path, current_path], False)
    write_bytes(output, json_bytes(report))
    write_bytes(current_path.parent / "pattern-report.json", json_bytes(patterns_report(current)))


if __name__ == "__main__":
    main()
