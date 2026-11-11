"""Record the hardware observation for the note bits test."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_note_bits_test import DECISION
from scripts.prepare_note_bits_test import DIRECTORY, REGISTRATION

ROOT = Path(__file__).resolve().parents[1]
EXPORT = "exported-note-bits-001"


def main():
    folder = ROOT / "experiments" / DIRECTORY
    registration_path = ROOT / "experiments" / REGISTRATION
    decision_path = ROOT / "experiments" / DECISION
    native_path = folder / "hardware-recapture-results-001.json"
    measure_path = folder / "note-bits-measurements-001.json"
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [native_path, measure_path, decision_path], False)
    native = json.loads(native_path.read_text())
    measurements = json.loads(measure_path.read_text())
    decision = json.loads(decision_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    report = json.loads((ROOT / "experiments" / EXPORT / "export-report.json").read_text())
    checks = {
        "native_check_passed": native["passed"],
        "capture_pin_matches": sha256_file(folder / "capture.wav") == native["capture_sha256"],
        "registration_pin_matches": sha256_file(registration_path)
        == native["registration_sha256"]
        == decision["registration_sha256"],
        "playback_matches_measurements": sha256_file(folder / "playback.wav")
        == measurements["playback_sha256"],
        "decision_binds_measurements": decision["measurements_sha256"] == sha256_file(measure_path),
        "export_checks_pass": all(report["checks"].values()),
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "note-bits-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Reception of pitch-code-0 notes and bit-5 flagged notes, and their measured pitch, level and duration",
                "checks": checks,
                "reception": decision["reception"],
                "bit5_stored": decision["bit5_stored"],
                "pitch": decision["pitch"],
                "bit5_inert": decision["bit5_inert"],
                "bit5_comparisons": decision["bit5_comparisons"],
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
        capture_status=f"validated_note_bits_{decision['reception']}_{decision['pitch']['classification']}",
        hardware_restore={"status": decision["reception"]},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        note_bits_measurements=measure_path.name,
        hardware_observation=observation_path.name,
        project=f"../{EXPORT}/project.json",
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(
        json.dumps(
            {
                "checks": all(checks.values()),
                "reception": decision["reception"],
                "pitch": decision["pitch"]["classification"],
                "bit5_inert": decision["bit5_inert"],
            }
        )
    )


if __name__ == "__main__":
    main()
