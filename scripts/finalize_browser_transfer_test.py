"""Record the hardware observation for the browser-transfer test, held and failed predictions alike."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_browser_transfer_test import IMPORT_RESULTS
from scripts.prepare_browser_transfer_test import DIRECTORY, IMPORTED, REGISTRATION

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / "experiments" / DIRECTORY
    registration_path = ROOT / "experiments" / REGISTRATION
    native_path = folder / "hardware-recapture-results-001.json"
    import_path = folder / IMPORT_RESULTS
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [native_path, import_path], False)
    native = json.loads(native_path.read_text())
    imported = json.loads(import_path.read_text())
    registration = json.loads(registration_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    checks = {
        "capture_pin_matches": sha256_file(folder / "capture.wav") == native["capture_sha256"],
        "registration_pin_matches": sha256_file(registration_path) == native["registration_sha256"]
        == imported["registration_sha256"],
        "imported_archive_pin_matches": sha256_file(folder / IMPORTED) == imported["imported_archive_sha256"],
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    held = {
        "send": native["passed"] and session["result"]["native_target_exact"] is True,
        "import": imported["passed"],
    }
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "browser-transfer-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "The web app's Send (a restore played by the browser) and Import (a backup recorded and decoded in the browser), on the device; a failed prediction is kept as failed",
                "checks": checks,
                "predictions": registration["predictions"],
                "held": held,
                "send_checks": native["checks"],
                "import_checks": imported["checks"],
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
        capture_status="browser_send_" + ("exact" if held["send"] else "failed") + "_import_" + ("held" if held["import"] else "failed"),
        hardware_restore={"status": "browser_send_verified_exact" if held["send"] else "browser_send_failed"},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        import_results=import_path.name,
        hardware_observation=observation_path.name,
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"held": held, "checks": all(checks.values())}))


if __name__ == "__main__":
    main()
