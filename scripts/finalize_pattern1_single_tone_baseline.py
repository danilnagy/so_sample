"""Record the hardware observation for the single-tone measurement baseline.

Run after the native and --audio checks of check_pattern1_single_tone_baseline have
passed. Binds the capture, analysis, playback, check reports, harness session records
and read-only export by hash, writes manual-observation.json and
hardware-observation-001.json once, and updates experiment.json's status fields.

The one-tone-per-loop count below is a supplementary measurement made after the data
arrived. It is not part of the frozen first-tone method and does not replace it.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import encode_packets
from po33_re.project import packets_from_view

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = "edited-pattern1-single-tone-no-FX-001"
EXPORT = "exported-pattern1-single-tone-no-FX-001"
REGISTRATION = "pattern1-single-tone-FX-order-baseline-registration-001.json"


def tone_onsets(path, block_seconds=0.005, relative=0.25, merge_seconds=0.3):
    samples, rate = sf.read(path, always_2d=True)
    envelope = np.abs(samples).max(axis=1)
    block = round(block_seconds * rate)
    count = len(envelope) // block
    peaks = envelope[: count * block].reshape(count, block).max(axis=1)
    active = peaks > relative * peaks.max()
    starts = np.flatnonzero(active[1:] & ~active[:-1]) + 1
    onsets = []
    for start in starts:
        if not onsets or (start - onsets[-1]) * block_seconds > merge_seconds:
            onsets.append(int(start))
    return [round(s * block / rate, 4) for s in onsets]


def main():
    folder = ROOT / "experiments" / EXPERIMENT
    export = ROOT / "experiments" / EXPORT
    registration_path = ROOT / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    native_path = folder / "hardware-recapture-results-001.json"
    audio_path = folder / "first-tone-results-001.json"
    capture, playback = folder / "capture.wav", folder / "playback.wav"
    artifact = folder / "derived/analysis-001/capture.symbols.npz"
    manual_path = folder / "manual-observation.json"
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([manual_path, observation_path], [native_path, audio_path], False)
    native = json.loads(native_path.read_text())
    audio = json.loads(audio_path.read_text())
    report = json.loads((export / "export-report.json").read_text())
    sessions = sorted(folder.glob("hardware-session-*.json"))
    session_records = {p.name: json.loads(p.read_text()) for p in sessions}
    restore_session = next(
        name
        for name, record in session_records.items()
        if record.get("result", {}).get("native_target_exact") is True
    )
    playback_session = next(
        name
        for name, record in session_records.items()
        if record.get("kind") == "playback_only" and (record.get("playback") or {}).get("file")
    )
    samples, rate = sf.read(capture, always_2d=True)
    played, played_rate = sf.read(playback, always_2d=True)
    onsets = tone_onsets(playback)
    intervals = np.diff(onsets)
    checks = {
        "native_check_passed": native["passed"] and all(native["checks"].values()),
        "audio_check_passed": audio["passed"] and all(audio["checks"].values()),
        "capture_and_artifact_pins_match": sha256_file(capture) == native["capture_sha256"]
        and sha256_file(artifact) == native["artifact_sha256"]
        and sha256_file(registration_path) == native["registration_sha256"],
        "playback_identity_matches_audio_report": sha256_file(playback) == audio["source_sha256"],
        "body_matches_registered_target": native["native_frame"]["encoded_body_sha256"]
        == registration["expected_body_sha256"],
        "export_hashes_and_native_body_exact": all(report["checks"].values())
        and all(
            sha256_file(export / name) == item["sha256"] for name, item in report["files"].items()
        )
        and hashlib.sha256(
            encode_packets(
                packets_from_view(json.loads((export / "source/packets.json").read_text()))
            )
        ).hexdigest()
        == registration["expected_body_sha256"],
        "capture_not_clipped": bool(np.all(np.abs(samples) < 1)),
        "playback_not_clipped": bool(np.all(np.abs(played) < 1)),
        "accepted_capture_is_harness_attempt": sha256_file(capture)
        == sha256_file(
            folder / "attempts" / session_records[restore_session]["accepted"]["attempt"]
        ),
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    answers = [
        o
        for record in session_records.values()
        for o in record.get("observations", [])
        if o.get("answer")
    ]
    write_bytes(
        manual_path,
        json_bytes(
            {
                "user_report": "Reported that the restore and the playback recording worked",
                "session_answers": answers,
                "one_tone_per_loop_confirmation": None,
                "interpretation": "No explicit listening answer was supplied in the session "
                "questions; the person reported completion only",
                "capture_sha256": native["capture_sha256"],
                "playback_sha256": audio["source_sha256"],
            }
        ),
    )
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "single-tone-baseline-native-and-audio-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Exact single-tone native target received; the unchanged "
                "frozen first-tone method finds a usable first tone in all six measurements",
                "checks": checks,
                "capture_sha256": native["capture_sha256"],
                "artifact_sha256": native["artifact_sha256"],
                "body_sha256": native["native_frame"]["encoded_body_sha256"],
                "native_results_sha256": sha256_file(native_path),
                "audio_results_sha256": sha256_file(audio_path),
                "manual_observation_sha256": sha256_file(manual_path),
                "playback_sha256": audio["source_sha256"],
                "harness_sessions": {
                    name: sha256_file(folder / name) for name in sorted(session_records)
                },
                "restore_session": restore_session,
                "playback_session": playback_session,
                "first_tone": {
                    "frequency_hz": audio["channels"]["left"]["measurements"][0]["fit"][
                        "frequency_hz"
                    ],
                    "onset_seconds": audio["channels"]["left"]["measurements"][0][
                        "first_onset_seconds"
                    ],
                },
                "supplementary_loop_measurement": {
                    "method": "envelope onsets above 25% of peak in 5 ms blocks, merged within 0.3 s; "
                    "chosen after the data arrived, not part of the frozen method",
                    "onsets_seconds": onsets,
                    "median_interval_seconds": float(np.median(intervals)),
                    "tones_per_interval": 1,
                },
                "capture_level": {
                    "sample_rate_hz": rate,
                    "peaks_per_channel": np.max(np.abs(samples), axis=0).tolist(),
                },
                "playback_level": {
                    "sample_rate_hz": played_rate,
                    "duration_seconds": len(played) / played_rate,
                    "peaks_per_channel": np.max(np.abs(played), axis=0).tolist(),
                },
                "new_effect_order_adjudicated": False,
                "per_step_nibble_order_confirmed": False,
                "general_per_step_FX_writer_enabled": False,
                "limits": [
                    "Establishes a usable unshifted single-tone reference, not the effect nibble order",
                    "The earlier F6/6F comparison stays inconclusive and unchanged",
                    "Earlier failed harness sessions and attempts are retained in attempts/",
                ],
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status="validated_exact_native_and_usable_single_tone",
        hardware_restore={"status": "verified_exact_native_target"},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        audio_results=audio_path.name,
        manual_observation=manual_path.name,
        hardware_observation=observation_path.name,
        project=f"../{EXPORT}/project.json",
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"checks": checks, "onsets": onsets}, indent=2))


if __name__ == "__main__":
    main()
