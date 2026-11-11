"""Record the hardware observation for the device-side effect code map.

Run after check_fx_code_map. Writes hardware-observation-001.json once and updates
experiment.json.
"""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_fx_code_map import RESULT
from scripts.prepare_fx_code_map import DIRECTORY

ROOT = Path(__file__).resolve().parents[1]
EXPORT = "exported-FX-code-map-001"


def main():
    folder = ROOT / "experiments" / DIRECTORY
    result_path = ROOT / "experiments" / RESULT
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [result_path], False)
    result = json.loads(result_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    report = json.loads((ROOT / "experiments" / EXPORT / "export-report.json").read_text())
    checks = {
        "capture_pin_matches": result["capture_sha256"] == sha256_file(folder / "capture.wav"),
        "artifact_pin_matches": result["artifact_sha256"]
        == sha256_file(folder / "derived/analysis-001/capture.symbols.npz"),
        "export_checks_pass": all(report["checks"].values()),
    }
    if not all(checks.values()):
        raise ValueError(f"Finalization checks failed: {checks}")
    records = [c for c in result["other_changes"] if c["region"] == "record"]
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "FX-code-map-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Device-recorded effect codes read from one backup",
                "checks": checks,
                "classification": result["classification"],
                "map_key_to_code": {k: v["mapped_code"] for k, v in result["keys"].items()},
                "all_patterns_uniform_16_steps": all(
                    v["steps_with_effect"] == 16 for v in result["keys"].values()
                ),
                "result_sha256": sha256_file(result_path),
                "capture_sha256": result["capture_sha256"],
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
                "other_record_changes": [item for c in records for item in c["bytes"]],
                "hypothesis_not_tested": "Second 0x7d5c record: byte 0 = selected pattern "
                "(0-based); bytes 131..146 = one byte per pattern 1..16, possibly the step "
                "where playback last stopped",
                "general_per_step_FX_writer_enabled": False,
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status=f"validated_FX_code_map_{result['classification']}",
        analysis="derived/analysis-001",
        result="../" + RESULT,
        hardware_observation=observation_path.name,
        project=f"../{EXPORT}/project.json",
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"checks": all(checks.values()), "classification": result["classification"]}))


if __name__ == "__main__":
    main()
