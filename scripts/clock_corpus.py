"""Check measured-clock recovery against the existing source-matched native corpus."""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.clock_decode import decode_clock_wav
from po33_re.modem.symbols import load_artifact


def main():
    root = Path(__file__).resolve().parents[1]
    corpus = json.loads((root / "experiments/packet-corpus-002.json").read_text())
    registered = {
        e["path"]: e["sha256"]
        for e in json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    }
    records = []
    for entry in corpus["records"]:
        if not entry.get("source_wav_matches_registered_hash") or not entry.get(
            "exact_body_reencode"
        ):
            continue
        path, artifact_path = root / entry["source_capture"], root / entry["artifact"]
        digest = sha256_file(path)
        if digest != registered[entry["source_capture"]] or digest != entry["source_sha256"]:
            raise ValueError("Corpus source no longer matches its registered hash")
        record = {
            "source_capture": entry["source_capture"],
            "source_sha256": digest,
            "acquisition_artifact_sha256": sha256_file(artifact_path),
        }
        try:
            acquisition = load_artifact(artifact_path)
            unchanged = acquisition.to_bytes()
            artifact, report = decode_clock_wav(path, acquisition)
            frame = report["native_frame"]
            record.update(
                passed=frame["encoded_body_sha256"] == entry["encoded_body_sha256"],
                exact_existing_body_hash_match=frame["encoded_body_sha256"]
                == entry["encoded_body_sha256"],
                acquisition_artifact_preserved=acquisition.to_bytes() == unchanged,
                native_frame=frame,
                clock_artifact_sha256=hashlib.sha256(artifact.to_bytes()).hexdigest(),
                channels={
                    ch: {
                        k: report["channels"][ch][k]
                        for k in (
                            "alignment",
                            "quarter_mismatches",
                            "original_crossing_label_mismatches",
                        )
                    }
                    for ch in ("left", "right")
                },
            )
        except ValueError as exc:
            record.update(passed=False, failure=str(exc))
        records.append(record)
        print(entry["source_capture"], record["passed"], flush=True)
    result = {
        "analysis_version": "amplitude-clock-corpus-0.1",
        "records": records,
        "passed_frames": sum(r["passed"] for r in records),
        "failed_frames": sum(not r["passed"] for r in records),
        "validated_packet_checks_total": sum(
            r["native_frame"]["packet_count"] for r in records if r["passed"]
        ),
        "target_data_used_for_decoding": False,
        "limits": [
            "Body hashes are compared only after independent recovery; no target data or corpus packet bytes select clock alignment.",
            "Counts include equivalent repeats and are not independent hardware tests.",
            "Original source captures, reviewed crossing artifacts and historical default-threshold failures remain unchanged.",
        ],
    }
    output = root / "experiments/amplitude-clock-corpus-001.json"
    validate_outputs([output], [], False)
    write_bytes(output, json_bytes(result))
    if result["failed_frames"]:
        raise ValueError(
            "Some existing frames did not pass bounded clock recovery; report retained"
        )


if __name__ == "__main__":
    main()
