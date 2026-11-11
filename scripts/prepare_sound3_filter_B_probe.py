"""Register an unknown FILTER B minimum with separate third-byte masks."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.filters import calibrated_sound3_filters
from po33_re.formats.packets import decode_artifact
from po33_re.modem.symbols import load_artifact

CAPTURE_ID = "event-062-a-sound3-filter-B-lock-down"
REGISTRATION = "sound3-filter-B-minimum-registration-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-sound3-filter63-center-001"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    source_path = root / observation["artifact_path"]
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(source_path) != observation["artifact_sha256"]
        or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
        or calibrated_sound3_filters(decode_artifact(load_artifact(source_path))) != (63,) * 16
    ):
        raise ValueError("Verified generated center63 and unfiltered listening required")
    directory = root / "experiments" / CAPTURE_ID
    registration_path = root / "experiments" / REGISTRATION
    if directory.exists() or directory.is_symlink() or registration_path.exists():
        raise ValueError("Fresh FILTER B registration and capture directory required")
    limits = [
        "B resonance location is a new hypothesis; third-primary bits2..6 and bits2..7 remain separate masks; bit7 is not declared a resonance bit or event flag",
        "Endpoint code and entire resulting body are unknown; no zero, uniformity, range, audible difference or numeric display reading is predicted",
        "A remains physically at center and stored63; coupled A changes are retained as a broader FILTER snapshot, not rescued as strict B support",
        "Current baseline precedes the already confirmed ordinary playback; any unrelated change is retained without attributing it solely to B",
        "Raw5/6-bit projections, bit7 and ramps remain literal; neutral cutoff may have no audible response to B",
        "Existing public filter guards remain unchanged and reject unfamiliar third-byte contexts; no resonance writer is enabled",
    ]
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "FILTER-B-counterclockwise-location-preregistration-0.1",
                "hardware_verified": False,
                "registered_before_B_minimum_capture": True,
                "experiment_id": CAPTURE_ID,
                "source_artifact": observation["artifact_path"],
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": observation["body_sha256"],
                "source_observation_sha256": sha256_file(observation_path),
                "expected_packet_count": 815,
                "expected_frame_end_byte": 156758,
                "candidate": {
                    "pattern": 1,
                    "sound": 3,
                    "second_primary_mask": 240,
                    "third_primary_mask": 3,
                },
                "broader_FILTER_candidate": {"second_primary_mask": 240, "third_primary_mask": 255},
                "B_candidate_masks": {
                    "third_primary_bits2_to6": 124,
                    "third_primary_bits2_to7": 252,
                },
                "expected_pitch_values": [14] * 16,
                "expected_volume_values": [36] * 16,
                "expected_filter_A_values": [63] * 16,
                "expected_B_endpoint_code": None,
                "recorded_action": "Pattern1/Sound3/FILTER playback, hold WRITE and move only B fully counterclockwise over5 seconds; hold3 seconds stationary, release/stop/write off, capture full backup; A stays untouched",
                "official_control_source": "https://teenage.engineering/guides/po-33/en",
                "limits": limits,
            }
        ),
    )
    directory.mkdir()
    write_bytes(
        directory / "experiment.json",
        json_bytes(
            {
                "experiment_id": CAPTURE_ID,
                "capture_status": "awaiting_recorded_FILTER_B_counterclockwise_probe",
                "registration": "../" + REGISTRATION,
                "planned_actions": [
                    "Keep Pattern1/Sound3/FILTER, A and audio settings unchanged",
                    "Start playback, hold WRITE and slowly turn only B fully counterclockwise over5 seconds; hold WRITE3 more seconds stationary",
                    "Release WRITE, stop playback and ensure write off; save complete capture.wav at established reduced level with one second trailing silence",
                    "Report actual audible/display changes or no change; leave B at minimum and A untouched; no restore or separate playback recording needed",
                ],
            }
        ),
    )
    write_bytes(
        directory / "instructions.md",
        b"# FILTER B counterclockwise probe\n\nKeep Pattern1/Sound3/FILTER selected, A and audio settings unchanged. Start playback,\nhold WRITE and move only B fully counterclockwise over about5 seconds. Hold WRITE\n3 more seconds with knobs stationary, release WRITE, stop and ensure write off.\nSave a complete backup as capture.wav here at the established reduced level with\none second trailing silence. Report actual audible/display changes, including no\nchange. Leave B at minimum and A untouched. No restore or separate playback.wav.\nDo not press keyboard keys or hold BPM/FX during the pass.\n",
    )
    print(json.dumps({"registered": True, "next_capture": CAPTURE_ID, "B_endpoint_unknown": True}))


if __name__ == "__main__":
    main()
