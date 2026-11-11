"""Record the voice stealing observation: registered readings plus the corrected re-read."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_voice_steal_exploratory import EXPLORATORY
from scripts.check_voice_steal_test import DECISION
from scripts.prepare_voice_steal_test import DIRECTORY, REGISTRATION

ROOT = Path(__file__).resolve().parents[1]
EXPORT = "exported-voice-steal-001"


def main():
    folder = ROOT / "experiments" / DIRECTORY
    registration_path = ROOT / "experiments" / REGISTRATION
    decision_path = ROOT / "experiments" / DECISION
    exploratory_path = ROOT / "experiments" / EXPLORATORY
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "voice-steal-measurements-001.json"
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs(
        [observation_path], [native_path, measure_path, decision_path, exploratory_path], False
    )
    native = json.loads(native_path.read_text())
    measurements = json.loads(measure_path.read_text())
    decision = json.loads(decision_path.read_text())
    exploratory = json.loads(exploratory_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    report = json.loads((ROOT / "experiments" / EXPORT / "export-report.json").read_text())
    checks = {
        "native_check_passed": native["passed"] and all(native["checks"].values()),
        "capture_pin_matches": sha256_file(folder / "capture.wav") == native["capture_sha256"],
        "registration_pin_matches": sha256_file(registration_path)
        == native["registration_sha256"]
        == decision["registration_sha256"],
        "playback_matches_measurements": sha256_file(folder / "playback.wav")
        == measurements["playback_sha256"]
        == exploratory["playback_sha256"],
        "decision_binds_measurements": decision["measurements_sha256"] == sha256_file(measure_path),
        "export_checks_pass": all(report["checks"].values()),
        "session_target_exact": session["result"]["native_target_exact"] is True,
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "voice-steal-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Exact native reception of four overflow scenarios; registered long-note readings invalid (wrong predicted frequency), corrected exploratory re-read recorded",
                "checks": checks,
                "registered_classification": decision["classification"],
                "registration_error": exploratory["registration_error"],
                "exploratory_present_by_step": {
                    k: v["present"] for k, v in exploratory["steps"].items()
                },
                "exploratory_reading": exploratory["reading"],
                "first_session_not_restored": "session 001's restore was not taken by the device; the backup equalled the previous state and was archived",
                "decision_sha256": sha256_file(decision_path),
                "exploratory_sha256": sha256_file(exploratory_path),
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
        capture_status="validated_exact_native_voice_steal_registered_invalid_exploratory_recorded",
        hardware_restore={"status": "verified_exact_native_target"},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        voice_steal_measurements=measure_path.name,
        hardware_observation=observation_path.name,
        project=f"../{EXPORT}/project.json",
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"checks": all(checks.values())}))


if __name__ == "__main__":
    main()
