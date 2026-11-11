"""Record the hardware observation for the web template test."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.prepare_web_template_test import DIRECTORY, REGISTRATION

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / "experiments" / DIRECTORY
    registration_path = ROOT / "experiments" / REGISTRATION
    native_path = folder / "hardware-recapture-results-001.json"
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [native_path], False)
    native = json.loads(native_path.read_text())
    registration = json.loads(registration_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    checks = {
        "native_check_passed": native["passed"] and all(native["checks"].values()),
        "capture_pin_matches": sha256_file(folder / "capture.wav") == native["capture_sha256"],
        "registration_pin_matches": sha256_file(registration_path) == native["registration_sha256"],
        "session_target_exact": session["result"]["native_target_exact"] is True,
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "web-template-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Exact native reception of a restore compiled by the TypeScript core from the empty-device template, with shared, referenced, embedded, sliced and absent sample records",
                "checks": checks,
                "predictions": registration["predictions"],
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
                "session_answers": [o for o in session["observations"] if o["answer"]],
                "limits": registration["limits"],
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status="validated_exact_native_web_template",
        hardware_restore={"status": "verified_exact_native_target"},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        hardware_observation=observation_path.name,
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"checks": all(checks.values()), "answers": len(checks)}))


if __name__ == "__main__":
    main()
