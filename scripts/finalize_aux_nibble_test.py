"""Record the hardware observation for the aux-nibble test, held and failed predictions alike."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_aux_nibble_test import DECISION
from scripts.prepare_aux_nibble_test import DIRECTORY, REGISTRATION

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / "experiments" / DIRECTORY
    registration_path = ROOT / "experiments" / REGISTRATION
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "aux-nibble-measurements-001.json"
    decision_path = ROOT / "experiments" / DECISION
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [native_path, measure_path, decision_path], False)
    native = json.loads(native_path.read_text())
    decision = json.loads(decision_path.read_text())
    registration = json.loads(registration_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    checks = {
        "native_check_passed": native["passed"] and all(native["checks"].values()),
        "capture_pin_matches": sha256_file(folder / "capture.wav") == native["capture_sha256"],
        "registration_pin_matches": sha256_file(registration_path) == native["registration_sha256"]
        == decision["registration_sha256"],
        "measurements_pin_matches": sha256_file(measure_path) == decision["measurements_sha256"],
        "session_target_exact": session["result"]["native_target_exact"] is True,
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    held = [name for name, r in decision["predictions"].items() if r["holds"]]
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "aux-nibble-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Exact native reception of raw auxiliary high nibbles, and their measured effect on drum onsets and melodic note length; predictions that failed are kept as failed",
                "checks": checks,
                "predictions": registration["predictions"],
                "held": held,
                "failed": [name for name in decision["predictions"] if name not in held],
                "drum_own_step_onsets_by_nibble": decision["drum_own_step_onsets_by_nibble"],
                "melodic_duration_seconds_by_nibble": decision["melodic_duration_seconds_by_nibble"],
                "exploratory": decision["exploratory"],
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
        capture_status="validated_exact_native_aux_nibble",
        hardware_restore={"status": "verified_exact_native_target"},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        measurements=measure_path.name,
        hardware_observation=observation_path.name,
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"held": held, "checks": all(checks.values())}))


if __name__ == "__main__":
    main()
