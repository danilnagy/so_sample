"""Record the knob observation: turning Sound16's knobs without WRITE stored nothing."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_knob_observation import RESULT
from scripts.prepare_knob_observation import DIRECTORY

ROOT = Path(__file__).resolve().parents[1]
EXPORT = "exported-sound-knobs-001"


def main():
    folder = ROOT / "experiments" / DIRECTORY
    result_path = ROOT / "experiments" / RESULT
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [result_path], False)
    result = json.loads(result_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    checks = {
        "backup_decoded": session["result"]["backup_decoded"],
        "capture_pin_matches": sha256_file(folder / "capture.wav") == result["capture_sha256"],
        "export_checks_pass": all(
            json.loads((ROOT / "experiments" / EXPORT / "export-report.json").read_text())[
                "checks"
            ].values()
        ),
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "sound-knobs-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Where turning a sound's knobs without WRITE is stored",
                "outcome": result["outcome"],
                "checks": checks,
                "session_answers": [o for o in session["observations"] if o["answer"]],
                "reading": "Knobs A and B showed pitch and volume. With WRITE off, turning them changed no byte of the backup: the sound-level setting that unlocked steps use is live device state, not saved data",
                "result_sha256": sha256_file(result_path),
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status=f"validated_knob_observation_{result['outcome']}",
        hardware_restore={"status": "restored_known_state_before_device_action"},
        analysis="derived/analysis-001",
        result="../" + RESULT,
        hardware_observation=observation_path.name,
        project=f"../{EXPORT}/project.json",
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"checks": all(checks.values()), "outcome": result["outcome"]}))


if __name__ == "__main__":
    main()
