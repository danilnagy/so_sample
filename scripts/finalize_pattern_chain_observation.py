"""Record the pattern-chain observation (the person chained Pattern1 then Pattern2)."""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_pattern_chain_observation import RESULT
from scripts.prepare_pattern_chain_observation import DIRECTORY

ROOT = Path(__file__).resolve().parents[1]
EXPORT = "exported-pattern-chain-001"
ACTUAL_CHAIN = [1, 2]


def main():
    folder = ROOT / "experiments" / DIRECTORY
    result_path = ROOT / "experiments" / RESULT
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [result_path], False)
    result = json.loads(result_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    changes = result["global_byte_changes"]["1"]
    steps = result["playback"]["step_frequencies_hz"]
    silent_loops = [
        loop for loop in range(5) if all(steps[str(k)][loop] is None for k in range(1, 17))
    ]
    checks = {
        "only_globals_changed": result["chain_in_global_record_only"],
        "entries_and_length": changes == [[0, 4, 0], [1, 0, 1], [128, 1, 2]],
        "pattern1_on_loops_1_3_5": result["playback"]["loop_matches"]["chain_1_5"]
        == [True, False, True, False, True],
        "empty_pattern2_silent_on_loops_2_4": silent_loops == [1, 3],
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
                "analysis_version": "pattern-chain-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Device storage and playback of a two-pattern chain",
                "protocol_deviation": "The person chained Pattern1 then Pattern2 instead of the registered Pattern1 then Pattern5; Pattern2 is empty",
                "actual_chain": ACTUAL_CHAIN,
                "registered_hypotheses": {
                    "chain_in_global_record_only": result["chain_in_global_record_only"],
                    "chain_1_5": "not applicable: a different chain was made; its Pattern1 loops match",
                    "chain_5_1": False,
                },
                "checks": checks,
                "reading": "Second global record bytes 0.. hold the chain entries counted from zero and byte 128 holds the chain length; the selected pattern is a chain of one. Entries past the length can hold stale values in other backups.",
                "result_sha256": sha256_file(result_path),
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status="validated_chain_storage_entries_and_length",
        hardware_restore={"status": "restored_known_state_before_device_action"},
        analysis="derived/analysis-001",
        result="../" + RESULT,
        hardware_observation=observation_path.name,
        project=f"../{EXPORT}/project.json",
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"checks": all(checks.values())}))


if __name__ == "__main__":
    main()
