"""Compare the knob-dump backup with the registered target and classify the differences."""

import argparse
import json
import subprocess
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.prepare_audition_knob_dump import DIRECTORY, REGISTRATION

RESULT = "audition-knob-dump-result-001.json"


def classify(changes):
    regions = {
        "global_records": any(c["region"] == "global" for c in changes),
        "pattern_cells": any(c["region"] == "pattern" for c in changes),
        "sound_records": any(c["region"] == "sound" for c in changes),
    }
    if not any(regions.values()):
        return "nothing_stored", regions
    if sum(regions.values()) > 1:
        return "mixed", regions
    if regions["global_records"]:
        return "global_records_only", regions
    if regions["sound_records"]:
        return "sound_records_only", regions
    sounds = {c["where"].get("sound") for c in changes if c["region"] == "pattern"}
    return ("sound16_cells_only" if sounds == {16} else "mixed"), regions


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    folder = root / "experiments" / DIRECTORY
    result_path = root / "experiments" / RESULT
    restore = root / "experiments/observe-audition-locks-001/restore.wav"
    validate_outputs([result_path], [restore], False)
    if sha256_file(restore) != registration["restore_of_record_sha256"]:
        raise ValueError("The restore of record changed")
    attempts = []
    for wav in sorted(folder.glob("attempts/backup-*.wav")):
        run = subprocess.run(
            ["npx", "tsx", "scripts/check-backup.ts", str(wav), str(restore)],
            cwd=root / "web",
            check=True,
            capture_output=True,
            text=True,
        )
        attempts.append(
            {
                "file": wav.name,
                "sha256": sha256_file(wav),
                **json.loads(run.stdout.strip().splitlines()[-1]),
            }
        )
    decoded = [a for a in attempts if a.get("decoded")]
    if not decoded:
        raise ValueError("No backup attempt decoded")
    last = decoded[-1]
    outcome, regions = classify(last["changes"])
    result = {
        "analysis_version": "audition-knob-dump-result-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "decoder": "web",
        "attempt": last["file"],
        "capture_sha256": last["sha256"],
        "exact_target": last["exact_target"],
        "outcome": outcome,
        "prediction": registration["prediction"],
        "prediction_held": outcome == registration["prediction"],
        "regions": regions,
        "change_count": len(last["changes"]),
        "changes": last["changes"][:200],
        "attempts": [{k: v for k, v in a.items() if k != "changes"} for a in attempts],
    }
    write_bytes(result_path, json_bytes(result))
    print(
        json.dumps(
            {
                k: result[k]
                for k in ("attempt", "exact_target", "outcome", "prediction_held", "change_count")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
