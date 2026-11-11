"""Record hardware observations for the single-tone F6/6F effect-order pair.

Run after both --leg checks and --audio of check_pattern1_fx_order_single_tone. Writes
manual-observation.json and hardware-observation-001.json for each leg once, and updates
experiment.json status fields. The registered audio result is kept exactly as written.
"""

import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import encode_packets
from po33_re.project import packets_from_view
from scripts.check_pattern1_fx_order_single_tone import COMPARISON
from scripts.prepare_pattern1_fx_order_single_tone import REGISTRATION

ROOT = Path(__file__).resolve().parents[1]
EXPLORATORY = "pattern1-single-tone-FX-order-pitch-track-exploratory-001.json"


def main():
    registration_path = ROOT / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    comparison_path = ROOT / "experiments" / COMPARISON
    comparison = json.loads(comparison_path.read_text())
    exploratory_path = ROOT / "experiments" / EXPLORATORY
    exploratory = json.loads(exploratory_path.read_text())
    for leg, spec in registration["legs"].items():
        folder = ROOT / "experiments" / spec["directory"]
        export = ROOT / "experiments" / spec["directory"].replace("edited-", "exported-")
        native_path = folder / "hardware-recapture-results-001.json"
        audio_path = folder / "first-tone-results-001.json"
        manual_path = folder / "manual-observation.json"
        observation_path = folder / "hardware-observation-001.json"
        validate_outputs([manual_path, observation_path], [native_path, audio_path], False)
        native = json.loads(native_path.read_text())
        audio = json.loads(audio_path.read_text())
        session_path = max(folder.glob("hardware-session-*.json"))
        session = json.loads(session_path.read_text())
        report = json.loads((export / "export-report.json").read_text())
        checks = {
            "native_check_passed": native["passed"] and all(native["checks"].values()),
            "capture_pin_matches": sha256_file(folder / "capture.wav") == native["capture_sha256"],
            "registration_pin_matches": sha256_file(registration_path)
            == native["registration_sha256"],
            "playback_matches_audio_report": sha256_file(folder / "playback.wav")
            == audio["source_sha256"],
            "export_hashes_and_native_body_exact": all(report["checks"].values())
            and all(
                sha256_file(export / name) == item["sha256"]
                for name, item in report["files"].items()
            )
            and hashlib.sha256(
                encode_packets(
                    packets_from_view(json.loads((export / "source/packets.json").read_text()))
                )
            ).hexdigest()
            == spec["expected_body_sha256"],
            "session_target_exact": session["result"]["native_target_exact"] is True,
        }
        if not all(checks.values()):
            raise ValueError(f"Leg {leg}: finalization checks failed: {checks}")
        answers = [o for o in session["observations"] if o["answer"]]
        write_bytes(
            manual_path,
            json_bytes(
                {
                    "session_answers": answers,
                    "later_user_report": "The effect is a function of the machine: on the "
                    "first step it fades in",
                    "capture_sha256": native["capture_sha256"],
                    "playback_sha256": audio["source_sha256"],
                }
            ),
        )
        name = "a_F6" if leg == "a" else "b_6F"
        write_bytes(
            observation_path,
            json_bytes(
                {
                    "analysis_version": "single-tone-FX-order-leg-observation-0.1",
                    "hardware_verified": True,
                    "verified_scope": "Exact native reception of the registered leg; "
                    "registered audio pair result inconclusive",
                    "checks": checks,
                    "leg": leg,
                    "footer_byte0": spec["footer_byte0"],
                    "capture_sha256": native["capture_sha256"],
                    "body_sha256": native["native_frame"]["encoded_body_sha256"],
                    "native_results_sha256": sha256_file(native_path),
                    "audio_results_sha256": sha256_file(audio_path),
                    "audio_method_usable_for_this_leg": audio["passed"],
                    "pair_comparison_sha256": sha256_file(comparison_path),
                    "pair_classification": comparison["classification"],
                    "manual_observation_sha256": sha256_file(manual_path),
                    "harness_session": session_path.name,
                    "harness_session_sha256": sha256_file(session_path),
                    "exploratory_pitch_departures_ms": exploratory["departures_ms"][name],
                    "exploratory_pitch_track_sha256": sha256_file(exploratory_path),
                    "per_step_nibble_order_confirmed": False,
                    "general_per_step_FX_writer_enabled": False,
                    "limits": [
                        "The registered steady-tone comparison is inconclusive and unchanged",
                        "The pitch-track reading is exploratory, chosen after the data",
                    ],
                }
            ),
        )
        status_path = folder / "experiment.json"
        status = json.loads(status_path.read_text())
        status.update(
            capture_status="validated_exact_native_audio_pair_inconclusive",
            hardware_restore={"status": "verified_exact_native_target"},
            analysis="derived/analysis-001",
            native_results=native_path.name,
            audio_results=audio_path.name,
            manual_observation=manual_path.name,
            hardware_observation=observation_path.name,
            project=f"../{export.name}/project.json",
        )
        write_bytes(status_path, json_bytes(status), force=True)
        print(json.dumps({"leg": leg, "checks": all(checks.values())}))


if __name__ == "__main__":
    main()
