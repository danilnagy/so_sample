"""Record the full step map confirmation (-002): registered precondition failed on byte 131.

The new backup differs from the target only in byte 131 of the second 0x7d5c record,
7 -> 14, after the previous session stopped Pattern 1's playback. The registration
required an exact match, so its decision did not run. The playback is classified here
as exploratory with the frozen per-note-gate method; that does not change the result.
"""

import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.pattern1_fx_multi_step_pitch_method import decide, step_results
from scripts.pattern1_fx_note_gate_method import SETTINGS, note_tracks
from scripts.prepare_pattern1_fx_full_step_map import PREDICTIONS
from scripts.prepare_pattern1_fx_full_step_map_confirm import DIRECTORY, REGISTRATION

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / "experiments" / DIRECTORY
    registration_path = ROOT / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    native_path = folder / "hardware-recapture-results-001.json"
    observation_path = folder / "hardware-observation-001.json"
    exploratory_path = folder / "exploratory-pitch-classification-001.json"
    validate_outputs([observation_path, exploratory_path], [native_path], False)
    native = json.loads(native_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    accepted = next(b for b in session["backups"] if b["file"] == session["accepted"]["attempt"])
    differences = accepted["target"]["differences_from_target"]["changes"]
    tracks = note_tracks(folder / "playback.wav", SETTINGS)
    results = step_results(tracks, registration["reference_frequency_hz"], SETTINGS)
    exploratory = {
        "analysis_version": "FX-full-step-map-confirm-exploratory-0.1",
        "exploratory": True,
        "reason": "Registered decision did not run: the backup differed from the target in byte 131",
        "playback_sha256": sha256_file(folder / "playback.wav"),
        "steps": {
            str(k): {"median": v["median"]["class"], "per_loop": v["per_loop"]}
            for k, v in results.items()
        },
        **decide(results, PREDICTIONS, SETTINGS),
    }
    write_bytes(exploratory_path, json_bytes(exploratory))
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "FX-full-step-map-confirm-observation-0.1",
                "hardware_verified": False,
                "registered_result": "precondition_failed",
                "failed_checks": [k for k, v in native["checks"].items() if not v],
                "differences_from_target": differences,
                "interpretation": "Only byte 131 of the second 0x7d5c record changed (7 -> 14), "
                "after the previous session stopped Pattern 1's playback; consistent with the "
                "untested hypothesis that it stores the step where Pattern 1 last stopped",
                "native_results_sha256": sha256_file(native_path),
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
                "session_answers": [o for o in session["observations"] if o["answer"]],
                "exploratory_classification": exploratory["classification"],
                "exploratory_sha256": sha256_file(exploratory_path),
                "lesson": "Runs without a restore inherit playback-state bytes; registrations "
                "that require exact backups should restore first",
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status="registered_precondition_failed_byte131_exploratory_sequential",
        analysis="derived/analysis-001",
        native_results=native_path.name,
        hardware_observation=observation_path.name,
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"exploratory": exploratory["classification"]}))


if __name__ == "__main__":
    main()
