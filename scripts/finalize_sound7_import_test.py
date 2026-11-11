"""Record the hardware observation for the Sound7 sample import test."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_sound7_import_test import DECISION
from scripts.prepare_sound7_import_test import DIRECTORY, REGISTRATION

ROOT = Path(__file__).resolve().parents[1]
EXPORT = "exported-sound7-import-001"


def main():
    folder = ROOT / "experiments" / DIRECTORY
    registration_path = ROOT / "experiments" / REGISTRATION
    decision_path = ROOT / "experiments" / DECISION
    native_path = folder / "hardware-recapture-results-001.json"
    pitch_path = folder / "key-frequency-results-001.json"
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [native_path, pitch_path, decision_path], False)
    native = json.loads(native_path.read_text())
    pitch = json.loads(pitch_path.read_text())
    decision = json.loads(decision_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    report = json.loads((ROOT / "experiments" / EXPORT / "export-report.json").read_text())
    checks = {
        "native_check_passed": native["passed"] and all(native["checks"].values()),
        "capture_pin_matches": sha256_file(folder / "capture.wav") == native["capture_sha256"],
        "registration_pin_matches": sha256_file(registration_path)
        == native["registration_sha256"]
        == decision["registration_sha256"],
        "playback_matches_results": sha256_file(folder / "playback.wav")
        == pitch["playback_sha256"],
        "decision_binds_results": decision["frequency_results_sha256"] == sha256_file(pitch_path),
        "export_checks_pass": all(report["checks"].values()),
        "session_target_exact": session["result"]["native_target_exact"] is True,
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "sound7-import-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Exact native reception of a sample imported into Sound7 and registered per-step pitches",
                "checks": checks,
                "classification": decision["classification"],
                "measured_cents_by_step": decision["measured_cents"],
                "decision_sha256": sha256_file(decision_path),
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
                "session_answers": [o for o in session["observations"] if o["answer"]],
                "limits": json.loads(registration_path.read_text())["limits"],
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status=f"validated_exact_native_sound7_import_{decision['classification']}",
        hardware_restore={"status": "verified_exact_native_target"},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        pitch_results=pitch_path.name,
        hardware_observation=observation_path.name,
        project=f"../{EXPORT}/project.json",
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(
        json.dumps({"checks": all(checks.values()), "classification": decision["classification"]})
    )


if __name__ == "__main__":
    main()
