"""Measure the independently recorded Sound4 tone after strict native validation."""

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
    directory = root / "experiments/event-022-b-record-independent-sound4"
    evidence_path = root / "experiments/sound4-allocation-results-001.json"
    source_path = directory / "derived/analysis-001/capture.symbols.npz"
    output = root / "experiments/sound4-sample-analysis-001.json"
    validate_outputs([output], [evidence_path, source_path, directory / "capture.wav"], False)
    evidence = json.loads(evidence_path.read_text())
    if not evidence["control_passed"] or not all(evidence["hypothesis_checks"].values()):
        raise ValueError("Reviewed isolated independent-buffer evidence required")
    source = load_artifact(source_path)
    frame = decode_artifact(source)
    if (
        sha256_file(source_path) != evidence["artifact_sha256"]
        or source.metadata["source_sha256"] != evidence["capture_sha256"]
    ):
        raise ValueError("Sample artifact differs from reviewed allocation capture")
    data = sound_data(frame, 3)
    codes = np.frombuffer(data[9:], dtype=np.uint8)
    endpoint = int.from_bytes(data[4:8], "little")
    audio, preview = sound_at_48k(frame, 4)
    measurement = measure_tone(audio, 48000)
    report = {
        "analysis_version": "second-owned-buffer-sample-analysis-0.1",
        "allocation_evidence_sha256": sha256_file(evidence_path),
        "capture_sha256": evidence["capture_sha256"],
        "artifact_sha256": evidence["artifact_sha256"],
        "sound_slot": 4,
        "owner_id": 3,
        "header_hex": data[:9].hex(),
        "payload_sha256": hashlib.sha256(data).hexdigest(),
        "backing_code_count": len(codes),
        "stored_endpoint": endpoint,
        "codes_after_endpoint": len(codes) - endpoint,
        "nonzero_codes_after_endpoint": int(np.count_nonzero(codes[endpoint:])),
        "packet_payload_length_histogram": dict(
            Counter(len(frame.packets[i].payload) for i in sound_groups(frame)[3])
        ),
        "preview": preview,
        "independently_fitted_tone": measurement,
        "comparison_to_registered_input": {
            "input_frequency_hz": 1000,
            "measured_frequency_ratio": measurement["dominant_frequency_hz"] / 1000,
        },
        "hardware_verified": False,
        "limits": [
            "Frequency is fitted across the observed spectrum without restricting it to the registered1000Hz target",
            "The preview uses the existing nominal23437.5Hz codec and zero-start endpoint policy; no new device-rate or inclusivity rule is inferred",
            "Sample-buffer size and stored endpoint are distinct; one32768-code allocation does not establish a rounding or resizing formula",
            "Envelope timing includes manual record gating and silence; no exact native sample length is predicted from the half-second input",
        ],
    }
    write_bytes(output, json_bytes(report))


if __name__ == "__main__":
    main()
