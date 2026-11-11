"""Record the hardware observation for the over-limit sample-memory step, any outcome."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_sample_memory_step4 import DECISION
from scripts.prepare_sample_memory_step4 import DIRECTORY, REGISTRATION

ROOT = Path(__file__).resolve().parents[1]
EXPORT = "exported-sample-memory-004"


def main():
    folder = ROOT / "experiments" / DIRECTORY
    registration_path = ROOT / "experiments" / REGISTRATION
    decision_path = ROOT / "experiments" / DECISION
    native_path = folder / "hardware-recapture-results-001.json"
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [native_path, decision_path], False)
    native = json.loads(native_path.read_text())
    decision = json.loads(decision_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    export_report = ROOT / "experiments" / EXPORT / "export-report.json"
    checks = {
        "registration_pin_matches": sha256_file(registration_path)
        == native["registration_sha256"]
        == decision["registration_sha256"],
        "decision_binds_native": decision["native_results_sha256"] == sha256_file(native_path),
        "capture_pin_matches": native["capture_sha256"] is None
        or sha256_file(folder / "capture.wav") == native["capture_sha256"],
        "export_checks_pass": native["capture_sha256"] is None
        or all(json.loads(export_report.read_text())["checks"].values()),
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "sample-memory-observation-0.4",
                "hardware_verified": True,
                "verified_scope": "Device response to a 1019904-code restore, above the advertised 40 s",
                "checks": checks,
                "outcome": decision["outcome"],
                "hypothesis_supported": decision["hypothesis_supported"],
                "summary": native["summary"],
                "classification": decision.get("classification"),
                "measured_cents_by_step": decision.get("measured_cents"),
                "absolute": decision.get("absolute"),
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
        capture_status=f"validated_over_limit_restore_{decision['outcome']}",
        hardware_restore={"status": decision["outcome"]},
        native_results=native_path.name,
        hardware_observation=observation_path.name,
    )
    if native["capture_sha256"] is not None:
        status.update(analysis="derived/analysis-001", project=f"../{EXPORT}/project.json")
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"checks": all(checks.values()), "outcome": decision["outcome"]}))


if __name__ == "__main__":
    main()
