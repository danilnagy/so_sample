"""Read how the PO-33 stored a drum recording in Sound11, against the registered hypotheses."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, sound_data, sound_groups
from po33_re.formats.patterns import pattern_data
from po33_re.hardware.changes import describe_changes
from po33_re.modem.symbols import load_artifact
from scripts.prepare_drum11_record_observation import DIRECTORY, REGISTRATION, SOUND11_IDS

RESULT = "drum11-record-result-001.json"


def records(frame):
    return {sid: sound_data(frame, sid) for sid, indices in sound_groups(frame).items() if indices}


def header(data):
    return {
        "start": int.from_bytes(data[0:4], "little"),
        "end": int.from_bytes(data[4:8], "little"),
        "owner": data[8],
    }


def evaluate(baseline, actual):
    before, after = records(baseline), records(actual)
    new_owners = [
        sid
        for sid, data in after.items()
        if len(data) > 9 and data[8] == sid and before.get(sid) != data
    ]
    owner = new_owners[0] if len(new_owners) == 1 else None
    slices = {sid: after.get(sid) for sid in SOUND11_IDS}
    references = {
        sid: header(data) for sid, data in slices.items() if data is not None and len(data) >= 9
    }
    windows = sorted((r["start"], r["end"]) for r in references.values())
    lengths = [end - start for start, end in windows]
    owner_codes = len(after[owner]) - 9 if owner is not None else None
    hypotheses = {
        "new_self_owned_buffer": owner is not None,
        "sixteen_references": owner is not None
        and len(references) == 16
        and all(r["owner"] == owner for r in references.values())
        and all(len(slices[sid]) == 9 or sid == owner for sid in SOUND11_IDS),
        "equal_split": len(windows) == 16
        and windows[0][0] == 0
        and max(lengths) - min(lengths) <= 1
        and all(windows[i + 1][0] - windows[i][1] in (0, 1) for i in range(15)),
        "everything_else_unchanged": all(
            before.get(sid) == after.get(sid)
            for sid in set(before) | set(after)
            if sid not in SOUND11_IDS and sid != owner
        )
        and all(
            pattern_data(baseline, n)[:1024] == pattern_data(actual, n)[:1024] for n in range(1, 17)
        ),
    }
    return {
        "owner_sound_id": owner,
        "owner_capacity_codes": owner_codes,
        "owner_header": header(after[owner]) if owner is not None else None,
        "slice_references": {str(k): v for k, v in references.items()},
        "slice_windows": windows,
        "hypotheses": hypotheses,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    folder = root / "experiments" / DIRECTORY
    capture = folder / "capture.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    baseline_path = root / registration["baseline_artifact"]
    output = root / "experiments" / RESULT
    validate_outputs([output], [capture, artifact_path, baseline_path], False)
    if sha256_file(baseline_path) != registration["baseline_artifact_sha256"]:
        raise ValueError("Baseline artifact changed since registration")
    artifact = load_artifact(artifact_path)
    if artifact.metadata["source_sha256"] != sha256_file(capture):
        raise ValueError("Analysis artifact is not from capture.wav")
    baseline = decode_artifact(load_artifact(baseline_path))
    actual = decode_artifact(artifact)
    result = evaluate(baseline, actual)
    changes = describe_changes(baseline, actual)
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "drum11-record-result-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": sha256_file(capture),
                "artifact_sha256": sha256_file(artifact_path),
                **result,
                "all_changes": changes,
            }
        ),
    )
    print(
        json.dumps(
            {
                "owner": result["owner_sound_id"],
                "owner_capacity_codes": result["owner_capacity_codes"],
                "owner_header": result["owner_header"],
                "windows": result["slice_windows"][:4],
                "hypotheses": result["hypotheses"],
                "change_count": changes["change_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
