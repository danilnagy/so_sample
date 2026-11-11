"""Measure the new and retained sample buffers and record observed packet-page layout."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from po33_re.analysis.playback import measure_tone
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, sound_data, sound_groups
from po33_re.formats.samples import sound_at_48k
from po33_re.modem.symbols import load_artifact


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-024-b-rerecord-shared-sound4"
    evidence_path = root / "experiments/shared-sound4-rerecord-results-001.json"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, default=root / "experiments/shared-sound4-sample-analysis-001.json"
    )
    args = parser.parse_args()
    output = args.out
    validate_outputs([output], [evidence_path, artifact_path, directory / "capture.wav"], False)
    evidence = json.loads(evidence_path.read_text())
    if (
        not evidence["control_passed"]
        or not evidence["hypothesis_checks"]["old_full_buffer_transferred_to_self_owned_sound5"]
    ):
        raise ValueError("Matching reviewed buffer-transfer evidence required")
    artifact = load_artifact(artifact_path)
    frame = decode_artifact(artifact)
    if (
        sha256_file(artifact_path) != evidence["artifact_sha256"]
        or artifact.metadata["source_sha256"] != evidence["capture_sha256"]
    ):
        raise ValueError("Analysis source differs from reviewed recapture")
    groups, records = sound_groups(frame), []
    for selector in (0, 3, 4):
        data = sound_data(frame, selector)
        codes = np.frombuffer(data[9:], dtype=np.uint8)
        endpoint = int.from_bytes(data[4:8], "little")
        lengths = [len(frame.packets[i].payload) for i in groups[selector]]
        pages, remainder = divmod(len(codes), 4096)
        expected_lengths = ([255] * 16 + [25]) + ([255] * 16 + [16]) * (pages - 1) if pages else []
        record = {
            "selector_id": selector,
            "header_hex": data[:9].hex(),
            "capacity_codes": len(codes),
            "endpoint": endpoint,
            "codes_after_endpoint": len(codes) - endpoint,
            "nonzero_code_bytes_after_endpoint": int(np.count_nonzero(codes[endpoint:])),
            "payload_sha256": hashlib.sha256(data).hexdigest(),
            "packet_payload_length_histogram": dict(Counter(lengths)),
            "observed4096_page_packet_layout_matches": remainder == 0
            and lengths == expected_lengths,
            "page_count4096": pages,
            "capacity_is_power_of_two": bool(len(codes)) and len(codes) & (len(codes) - 1) == 0,
        }
        if selector in (3, 4):
            audio, preview = sound_at_48k(frame, selector + 1)
            record.update(preview=preview, independently_fitted_tone=measure_tone(audio, 48000))
        records.append(record)
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "shared-overwrite-sample-and-page-analysis-0.2",
                "packet_page_model": "First header+4096-code page split into sixteen255-byte payloads and one25-byte remainder; subsequent4096-code pages split into sixteen255-byte payloads and one16-byte remainder",
                "evidence_sha256": sha256_file(evidence_path),
                "capture_sha256": evidence["capture_sha256"],
                "artifact_sha256": evidence["artifact_sha256"],
                "buffers": records,
                "hardware_verified": False,
                "limits": [
                    "Page/chunk observations describe these retained packet layouts; they do not establish how new allocation capacity is selected",
                    "The73728-code buffer is not a power of two, so a universal power-of-two allocation assumption is not supported",
                    "Tone fits use the existing nominal-rate codec and endpoint preview policy, without forcing the recorded frequency",
                    "Tail code bytes are preserved; they are not normalized or interpreted as a particular allocator state",
                ],
            }
        ),
    )


if __name__ == "__main__":
    main()
