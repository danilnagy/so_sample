"""Record the audition-lock observation's outcome in the experiment folder."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_audition_lock_observation import MEASUREMENTS, RESULT
from scripts.prepare_audition_lock_observation import DIRECTORY

ROOT = Path(__file__).resolve().parents[1]
READINGS = {
    "audition_follows_last_lock": "After the pattern played, auditions by hand matched its locked notes: playing a pattern sets the live values",
    "audition_keeps_live_state": "Auditions by hand sounded the same before and after the pattern and differed from its locked notes: playing a pattern leaves the live values alone",
    "indistinguishable": "All three groups matched, so the live filter already was the bypass; the question is open",
    "other": "The groups fit none of the registered outcomes; see the measurements",
}


def main():
    folder = ROOT / "experiments" / DIRECTORY
    result_path = ROOT / "experiments" / RESULT
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [result_path, folder / MEASUREMENTS], False)
    result = json.loads(result_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    native = result["native"]
    backup = "capture.wav" if native["decoder"] == "harness" else f"attempts/{native['file']}"
    checks = {
        "backup_decoded": bool(session["result"]["backup_decoded"]) or native["decoder"] == "web",
        "native_target_exact": native["exact_target"],
        "capture_pin_matches": native["file"] is not None
        and sha256_file(folder / backup) == result["capture_sha256"],
        "playback_pin_matches": sha256_file(folder / result["playback_file"])
        == result["playback_sha256"],
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "audition-lock-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Whether auditioning a sound by hand follows the locks of a pattern that just played",
                "outcome": result["outcome"],
                "prediction": result["prediction"],
                "prediction_held": result["prediction_held"],
                "live_filter_before_pattern": result["live_filter_before_pattern"],
                "live_filter_after_pattern": result["live_filter_after_pattern"],
                "checks": checks,
                "native_decoder": native["decoder"],
                "exploratory": result.get("exploratory"),
                "playback_file": result["playback_file"],
                "session_answers": [o for o in session["observations"] if o["answer"]],
                "reading": READINGS[result["outcome"]],
                "result_sha256": sha256_file(result_path),
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status=f"validated_audition_lock_observation_{result['outcome']}",
        hardware_restore={"status": "verified_exact_native_target"},
        analysis="derived/analysis-001",
        measurements=MEASUREMENTS,
        result="../" + RESULT,
        hardware_observation=observation_path.name,
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(
        json.dumps(
            {
                "checks": all(checks.values()),
                "outcome": result["outcome"],
                "prediction_held": result["prediction_held"],
            }
        )
    )


if __name__ == "__main__":
    main()
