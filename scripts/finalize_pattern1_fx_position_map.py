"""Record the hardware observation for the footer position map.

Run after check_pattern1_fx_position_map. Writes manual-observation.json and
hardware-observation-001.json once and updates experiment.json.
"""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import encode_packets
from po33_re.project import packets_from_view
from scripts.check_pattern1_fx_position_map import DECISION
from scripts.prepare_pattern1_fx_position_map import DIRECTORY, REGISTRATION

ROOT = Path(__file__).resolve().parents[1]
EXPORT = "exported-pattern1-FX-position-map-001"


def main():
    folder = ROOT / "experiments" / DIRECTORY
    export = ROOT / "experiments" / EXPORT
    registration_path = ROOT / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    decision_path = ROOT / "experiments" / DECISION
    decision = json.loads(decision_path.read_text())
    native_path = folder / "hardware-recapture-results-001.json"
    pitch_path = folder / "pitch-track-results-001.json"
    manual_path = folder / "manual-observation.json"
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([manual_path, observation_path], [native_path, pitch_path], False)
    native = json.loads(native_path.read_text())
    pitch = json.loads(pitch_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    report = json.loads((export / "export-report.json").read_text())
    checks = {
        "native_check_passed": native["passed"] and all(native["checks"].values()),
        "capture_pin_matches": sha256_file(folder / "capture.wav") == native["capture_sha256"],
        "registration_pin_matches": sha256_file(registration_path)
        == native["registration_sha256"]
        == decision["registration_sha256"],
        "playback_matches_pitch_result": sha256_file(folder / "playback.wav")
        == pitch["playback_sha256"],
        "decision_binds_results": decision["pitch_results_sha256"] == sha256_file(pitch_path)
        and decision["native_results_sha256"] == sha256_file(native_path),
        "export_hashes_and_native_body_exact": all(report["checks"].values())
        and all(
            sha256_file(export / name) == item["sha256"] for name, item in report["files"].items()
        )
        and hashlib.sha256(
            encode_packets(
                packets_from_view(json.loads((export / "source/packets.json").read_text()))
            )
        ).hexdigest()
        == registration["expected_body_sha256"],
        "session_target_exact": session["result"]["native_target_exact"] is True,
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    write_bytes(
        manual_path,
        json_bytes(
            {
                "session_answers": [o for o in session["observations"] if o["answer"]],
                "capture_sha256": native["capture_sha256"],
                "playback_sha256": pitch["playback_sha256"],
            }
        ),
    )
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "FX-position-map-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Exact native reception and registered per-note pitch decision",
                "checks": checks,
                "footer": registration["footer"],
                "steps": decision["steps"],
                "classification": decision["classification"],
                "decision_sha256": sha256_file(decision_path),
                "native_results_sha256": sha256_file(native_path),
                "pitch_results_sha256": sha256_file(pitch_path),
                "manual_observation_sha256": sha256_file(manual_path),
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
                "general_per_step_FX_writer_enabled": False,
                "limits": registration["limits"],
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status=f"validated_exact_native_pitch_track_{decision['classification']}",
        hardware_restore={"status": "verified_exact_native_target"},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        pitch_results=pitch_path.name,
        manual_observation=manual_path.name,
        hardware_observation=observation_path.name,
        project=f"../{EXPORT}/project.json",
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(
        json.dumps({"checks": all(checks.values()), "classification": decision["classification"]})
    )


if __name__ == "__main__":
    main()
