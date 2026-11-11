"""Record the volume law run: exact reception, neither registered law, a measured gain table.

Volume code 0 played at the same level as the preceding step (volume 36) within 0.002 dB,
not silence; that observation is recorded for the follow-up test.
"""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_volume_law_test import DECISION
from scripts.prepare_volume_law_test import DIRECTORY, REGISTRATION

ROOT = Path(__file__).resolve().parents[1]
EXPORT = "exported-volume-law-001"


def main():
    folder = ROOT / "experiments" / DIRECTORY
    registration_path = ROOT / "experiments" / REGISTRATION
    decision_path = ROOT / "experiments" / DECISION
    native_path = folder / "hardware-recapture-results-001.json"
    level_path = folder / "level-results-001.json"
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [native_path, level_path, decision_path], False)
    native = json.loads(native_path.read_text())
    levels = json.loads(level_path.read_text())
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
        == levels["playback_sha256"],
        "decision_binds_results": decision["level_results_sha256"] == sha256_file(level_path),
        "export_checks_pass": all(report["checks"].values()),
        "session_target_exact": session["result"]["native_target_exact"] is True,
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    table = {
        k: round(v, 2)
        for k, v in sorted(decision["measured_db_by_code"].items(), key=lambda kv: int(kv[0]))
    }
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "volume-law-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Exact native reception and a measured per-step gain table "
                "at pitch 13; neither registered law holds",
                "checks": checks,
                "classification": decision["classification"],
                "measured_db_by_code_relative_to_36": table,
                "code0_observation": "Volume code 0 played at the preceding step's level "
                "(volume 36) within 0.002 dB in every loop, not silence",
                "decision_sha256": sha256_file(decision_path),
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
                "session_answers": [o for o in session["observations"] if o["answer"]],
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status="validated_exact_native_volume_gain_table_measured",
        hardware_restore={"status": "verified_exact_native_target"},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        level_results=level_path.name,
        hardware_observation=observation_path.name,
        project=f"../{EXPORT}/project.json",
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"checks": all(checks.values()), "table": table}))


if __name__ == "__main__":
    main()
