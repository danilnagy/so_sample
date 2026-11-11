"""Measure the audition-lock observation: native reception, then the three hit groups.

Native reception: the harness's own decode when it accepted one; otherwise every backup
attempt is decoded with the web app's decoder (web/scripts/check-backup.ts), which finds
the preamble past noise, and compared to the restore. The playback measured is the newest
retake's when one exists, else the session's own.
"""

import argparse
import json
import subprocess
from itertools import pairwise
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact
from scripts.audition_lock_method import SETTINGS, analyze
from scripts.prepare_audition_lock_observation import DIRECTORY, REGISTRATION

RESULT = "audition-lock-result-001.json"
MEASUREMENTS = "audition-measurements-001.json"


def silence_reading(folder, playback, report):
    """Exploratory, outside the frozen method: the level of the stretches between hit groups.

    Where the procedure called for auditions by hand, a stretch at the noise floor means
    the presses produced no output at all, which the method cannot classify.
    """
    samples, rate = sf.read(str(playback), always_2d=True)
    mono = samples.mean(axis=1)
    rms = lambda a, b: float(np.sqrt(np.mean(mono[round(a * rate) : round(b * rate)] ** 2)))
    times = report["hit_times_seconds"]
    groups = report["groups"]
    stretches = []
    if times:
        stretches.append(
            {"what": "before the first hit", "from": 0.3, "to": max(0.3, times[0] - 0.3)}
        )
        for a, b in pairwise(groups):
            stretches.append({"what": "between hit groups", "from": a[-1] + 0.6, "to": b[0] - 0.3})
    for s in stretches:
        s["rms"] = rms(s["from"], s["to"]) if s["to"] > s["from"] + 0.5 else None
    hits = [rms(t + 0.06, t + 0.22) for t in times]
    floor = rms(0.0, min(0.3, len(mono) / rate))
    # With more groups than the procedure has parts, the same measure over the first
    # three alone; the registered outcome stays what the whole recording gives.
    first_three = None
    if len(groups) > 3:
        cut = round((groups[3][0] - 0.5) * rate)
        truncated = playback.with_name(f"{playback.stem}-first-three-groups.wav")
        sf.write(str(truncated), samples[:cut], rate, subtype="PCM_16")
        partial = analyze(truncated, SETTINGS)
        first_three = {
            "file": truncated.relative_to(folder).as_posix(),
            "group_sizes": partial["group_sizes"],
            "outcome": partial["outcome"],
            "comparisons": partial.get("comparisons"),
            "band_means_db": {
                k: v["band_means_db"] for k, v in (partial.get("groups_by_name") or {}).items()
            },
            "hit_rms_by_group": [[round(hits[times.index(t)], 4) for t in g] for g in groups[:3]],
        }
    return {
        "label": "exploratory, not part of the registered method",
        "noise_floor_rms": floor,
        "hit_rms_median": float(np.median(hits)) if hits else None,
        "stretches": stretches,
        "first_three_groups": first_three,
        "reading": "every stretch where auditions by hand were due sits at the noise floor: the presses produced no output"
        if stretches and all(s["rms"] is not None and s["rms"] < 4 * floor for s in stretches)
        else None,
    }


def native_reception(root, folder, target_path):
    """Exact reception evidence: the harness decode, else the web decoder over every attempt."""
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    capture = folder / "capture.wav"
    if artifact_path.exists() and capture.exists():
        artifact = load_artifact(artifact_path)
        if artifact.metadata["source_sha256"] != sha256_file(capture):
            raise ValueError("Analysis artifact is not from capture.wav")
        actual, target = decode_artifact(artifact), decode_artifact(load_artifact(target_path))
        exact = actual.packets == target.packets and actual.encoded_body == target.encoded_body
        return {
            "decoder": "harness",
            "file": "capture.wav",
            "capture_sha256": sha256_file(capture),
            "exact_target": exact,
        }
    attempts = []
    for wav in sorted(folder.glob("attempts/backup-*.wav")):
        run = subprocess.run(
            ["npx", "tsx", "scripts/check-backup.ts", str(wav), str(folder / "restore.wav")],
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
    exact = next((a for a in attempts if a.get("exact_target")), None)
    return {
        "decoder": "web",
        "file": exact["file"] if exact else None,
        "capture_sha256": exact["sha256"] if exact else None,
        "exact_target": bool(exact),
        "attempts": attempts,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    if (
        sha256_file(root / "scripts/audition_lock_method.py")
        != registration["method_script_sha256"]
        or registration["method_settings"] != SETTINGS
    ):
        raise ValueError("Frozen method changed since registration")
    folder = root / "experiments" / DIRECTORY
    retakes = sorted(folder.glob("retake-*/playback.wav"))
    playback = retakes[-1] if retakes else folder / "playback.wav"
    # A retake may name the recording to measure, with its reason, when the accepted one
    # is not the attempt that followed the procedure.
    chosen = json.loads((playback.parent / "experiment.json").read_text()) if retakes else {}
    if chosen.get("measured_playback"):
        playback = playback.parent / chosen["measured_playback"]
    target_path = folder / "edited.symbols.npz"
    measure_path = folder / MEASUREMENTS
    result_path = root / "experiments" / RESULT
    validate_outputs([measure_path, result_path], [playback, target_path], False)
    if sha256_file(target_path) != registration["edited_artifact_sha256"]:
        raise ValueError("Registered target changed")
    native = native_reception(root, folder, target_path)
    report = analyze(playback, SETTINGS)
    exploratory = silence_reading(folder, playback, report)
    earlier = [p for p in [folder / "playback.wav", *retakes[:-1]] if p.exists() and p != playback]
    write_bytes(
        measure_path,
        json_bytes(
            {
                "analysis_version": "audition-lock-measurements-0.1",
                "hardware_verified": False,
                "playback_file": playback.relative_to(folder).as_posix(),
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                **report,
                "measured_playback_reason": chosen.get("measured_reason"),
                "exploratory": exploratory,
                "earlier_playbacks": [
                    {
                        "file": p.relative_to(folder).as_posix(),
                        "sha256": sha256_file(p),
                        "group_sizes": analyze(p, SETTINGS)["group_sizes"],
                    }
                    for p in earlier
                ],
            }
        ),
    )
    result = {
        "analysis_version": "audition-lock-result-0.1",
        "hardware_verified": False,
        "registration_sha256": sha256_file(registration_path),
        "capture_sha256": native["capture_sha256"],
        "playback_file": playback.relative_to(folder).as_posix(),
        "playback_sha256": sha256_file(playback),
        "native": native,
        "outcome": report["outcome"],
        "prediction": registration["prediction"],
        "prediction_held": report["outcome"] == registration["prediction"],
        "comparisons": report.get("comparisons"),
        "live_filter_before_pattern": report.get("live_filter_before_pattern"),
        "live_filter_after_pattern": report.get("live_filter_after_pattern"),
        "group_sizes": report["group_sizes"],
        "reason": report.get("reason"),
        "exploratory": exploratory,
    }
    write_bytes(result_path, json_bytes(result))
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "native",
                    "outcome",
                    "prediction_held",
                    "group_sizes",
                    "live_filter_before_pattern",
                    "live_filter_after_pattern",
                    "reason",
                )
            },
            indent=2,
        )
    )
    if not native["exact_target"]:
        raise ValueError("The backup differs from the restored target; result retained")


if __name__ == "__main__":
    main()
