"""Register a WRITE-mode FX7 pass against the current verified resonance32 state."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact

CAPTURE_ID = "event-065-a-pattern1-FX7-recorded"
REGISTRATION = "pattern1-FX7-probe-registration-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-sound3-filter16-B32-middle-001"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Verified resonance32 reception and frozen audio required")
    frame = decode_artifact(load_artifact(source_path))
    if pattern_data(frame, 1)[1024:] != bytes([255]) * 8:
        raise ValueError("Independent FF footer baseline required")
    directory = root / "experiments" / CAPTURE_ID
    registration_path = root / "experiments" / REGISTRATION
    if directory.exists() or directory.is_symlink() or registration_path.exists():
        raise ValueError("Fresh FX registration and capture folder required")
    limits = [
        "Footer bytes1024..1031 are a new location hypothesis; both high/low-first nibble projections remain literal and no raw FX7 code is guessed",
        "FX7 is official octave-up and requires write mode enabled, distinct from holding WRITE during knob automation",
        "Current source preceded already confirmed ordinary playback; probe includes that playback plus WRITE/FX pass, retaining unrelated changes without sole attribution",
        "No uniformity or whole target body is predicted; release timing may leave mixed footer values; no averages rescue failures",
        "Broader Pattern1 and nonpattern differences remain distinct; sample/parameter changes do not rescue footer-only support",
        "No public FX writer or interpretation of the complete effect/footer encoding is enabled",
    ]
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "Pattern1-recorded-FX7-footer-location-preregistration-0.1",
                "hardware_verified": False,
                "registered_before_recorded_FX_capture": True,
                "experiment_id": CAPTURE_ID,
                "source_artifact": observation["artifact_path"],
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": observation["body_sha256"],
                "source_observation_sha256": sha256_file(observation_path),
                "expected_packet_count": 815,
                "expected_frame_end_byte": 156758,
                "footer_candidate": {"pattern": 1, "start_byte": 1024, "bytes": 8},
                "raw_FX_code_prediction": None,
                "official_effect_key": 7,
                "official_effect_name": "octave_up",
                "official_control_source": "https://teenage.engineering/guides/po-33/en",
                "limits": limits,
            }
        ),
    )
    directory.mkdir()
    actions = [
        "Keep Pattern1 selected and both knobs plus audio settings unchanged; stop playback",
        "Press WRITE once to enable write mode and confirm its indicator",
        "Start playback; hold FX and key7 together for about8 seconds",
        "Release FX/key7, immediately stop playback, then switch write mode off",
        "Save a complete capture.wav here at established reduced level with one second trailing silence; report actual sound/display changes",
        "No knob movement, restore or separate playback recording needed; do not hold WRITE during FX pass or press other keyboard keys",
    ]
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": CAPTURE_ID,
                "capture_status": "awaiting_recorded_Pattern1_FX7_probe",
                "registration": "../" + REGISTRATION,
                "planned_actions": actions,
            }
        ),
    )
    write_bytes(
        directory / "instructions.md",
        (
            "# Recorded Pattern1 FX7 probe\n\n"
            + "\n".join(f"{index}. {action}" for index, action in enumerate(actions, 1))
            + "\n\nFX7 is octave-up according to the official guide; footer location and raw encoding remain unverified.\n"
        ).encode(),
    )
    print(json.dumps({"registered": True, "next_capture": CAPTURE_ID, "raw_FX_code_unknown": True}))


if __name__ == "__main__":
    main()
