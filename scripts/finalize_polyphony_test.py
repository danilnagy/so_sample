"""Record the polyphony observation: frozen method failure plus the exploratory reading."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_polyphony_exploratory import EXPLORATORY
from scripts.check_polyphony_test import DECISION
from scripts.prepare_polyphony_test import DIRECTORY, REGISTRATION

ROOT = Path(__file__).resolve().parents[1]
EXPORT = "exported-polyphony-001"


def main():
    folder = ROOT / "experiments" / DIRECTORY
    registration_path = ROOT / "experiments" / REGISTRATION
    decision_path = ROOT / "experiments" / DECISION
    exploratory_path = ROOT / "experiments" / EXPLORATORY
    native_path = folder / "hardware-recapture-results-001.json"
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [native_path, decision_path, exploratory_path], False)
    native = json.loads(native_path.read_text())
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
        "playback_matches_exploratory": sha256_file(folder / "playback.wav")
        == exploratory["playback_sha256"],
        "export_checks_pass": all(report["checks"].values()),
        "session_target_exact": session["result"]["native_target_exact"] is True,
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "polyphony-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Exact native reception of fourteen distinct sounds stacked on shared steps; the registered method failed to run and an exploratory reading counted the voices",
                "checks": checks,
                "registered_classification": decision["classification"],
                "frozen_method_error": decision["frozen_method_error"],
                "exploratory": {
                    "classification": exploratory["classification"],
                    "stacks": {
                        k: None
                        if v is None
                        else {
                            "requested": v["requested"],
                            "present": v["present"],
                            "count": v["count"],
                        }
                        for k, v in exploratory["stacks"].items()
                    },
                },
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
        capture_status="validated_exact_native_polyphony_method_failed_exploratory_4_voices",
        hardware_restore={"status": "verified_exact_native_target"},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        hardware_observation=observation_path.name,
        project=f"../{EXPORT}/project.json",
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(
        json.dumps({"checks": all(checks.values()), "exploratory": exploratory["classification"]})
    )


if __name__ == "__main__":
    main()
