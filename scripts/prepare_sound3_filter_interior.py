"""Register two physical FILTER interiors and an exact neutral-center return."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes

CAPTURE_IDS = (
    "event-059-f-sound3-filter-A-lowpass-interior",
    "event-060-g-sound3-filter-A-highpass-interior",
    "event-061-h-return-sound3-filter-A-center",
)
REGISTRATION = "sound3-filter-A-interior-registration-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "experiments/event-058-e-sound3-filter-A-center"
    observation_path = source / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    native_path = source / "center-native-results-001.json"
    audio_path = source / "center-audio-comparison-results-001.json"
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or observation["contiguous_candidate_values"] != [63] * 16
        or sha256_file(root / observation["artifact_path"]) != observation["artifact_sha256"]
        or sha256_file(source / "capture.wav") != observation["capture_sha256"]
        or sha256_file(native_path) != observation["native_results_sha256"]
        or sha256_file(audio_path) != observation["audio_comparison_results_sha256"]
    ):
        raise ValueError("Verified literal63 center and pinned evidence required")
    registration_path = root / "experiments" / REGISTRATION
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh interior registration and all three folders required")
    limits = [
        "Both previous between-endpoint center predictions failed at63; original reports and incorrect full-bar cue remain immutable",
        "Special neutral63 and two branches are new post-center hypotheses registered before these interior data",
        "Interior values and complete bodies are unknown; no exact quarter-position code or uniformity is predicted",
        "Two scalar branch-order projections remain distinct; failures, ramps, unchanged captures and wider changes are retained",
        "Whole independent center body and every packet must return exactly; matching candidate codes alone are insufficient",
        "Single middle tick is the user-confirmed center cue; interior UI units, cutoffHz, full width, resonance and public writer remain unconfirmed",
        "No ordinary audio measurement is required for these backups; user audibility and knob directions remain separate observations",
    ]
    legs = [
        {
            "experiment_id": CAPTURE_IDS[0],
            "physical_side": "counterclockwise_lowpass",
            "expected_raw_code": None,
        },
        {
            "experiment_id": CAPTURE_IDS[1],
            "physical_side": "clockwise_highpass",
            "expected_raw_code": None,
        },
        {
            "experiment_id": CAPTURE_IDS[2],
            "physical_side": "single_middle_tick_center_return",
            "expected_contiguous_values": [63] * 16,
            "expected_alternative_values": [63] * 16,
            "expected_complete_body_sha256": observation["body_sha256"],
        },
    ]
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "FILTER-two-interiors-and-exact-neutral-return-preregistration-0.1",
                "hardware_verified": False,
                "registered_before_all_three_captures": True,
                "model_revised_after_center63_observation": True,
                "source_artifact": observation["artifact_path"],
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (source / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": observation["body_sha256"],
                "source_observation_sha256": sha256_file(observation_path),
                "source_native_results_sha256": sha256_file(native_path),
                "source_audio_comparison_sha256": sha256_file(audio_path),
                "expected_packet_count": 815,
                "expected_frame_end_byte": 156758,
                "candidate": {
                    "pattern": 1,
                    "sound": 3,
                    "second_primary_mask": 240,
                    "third_primary_mask": 3,
                },
                "broader_FILTER_candidate": {"second_primary_mask": 240, "third_primary_mask": 255},
                "expected_pitch_values": [14] * 16,
                "expected_volume_values": [36] * 16,
                "expected_capture_sequence": legs,
                "branch_scalar_order_hypotheses": {
                    "contiguous": {
                        "lowpass_strict_bounds": [1, 32],
                        "highpass_strict_bounds": [31, 62],
                    },
                    "alternative": {
                        "lowpass_strict_bounds": [4, 32],
                        "highpass_strict_bounds": [31, 59],
                    },
                },
                "hypothesis_interpretation": "Special neutral63 with interior LPF/HPF in lower/upper numerical branches; these are falsifiable scalar-order hypotheses, not already decoded mode bits",
                "limits": limits,
            }
        ),
    )
    actions = [
        "From the current single-tick center move only A counterclockwise to about halfway toward fully counterclockwise (roughly one-quarter of total knob travel)",
        "Move only A clockwise to about halfway between center and fully clockwise (roughly three-quarters of total knob travel)",
        "Move only A back to the single middle tick where the whole sample sounds unfiltered",
    ]
    for directory, leg, action in zip(directories, legs, actions):
        directory.mkdir()
        planned = [
            "Keep Pattern1/Sound3/FILTER, B and all audio settings unchanged",
            "Start playback and hold WRITE; " + action + " over about5 seconds",
            "Hold WRITE3 more seconds stationary, release WRITE, stop playback and ensure write off",
            "Save complete capture.wav here at established reduced level with one second trailing silence before the next action",
            "Report actual audibility/display without guessing numeric codes; no separate playback.wav or restore is required",
        ]
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": leg["experiment_id"],
                    "capture_status": "awaiting_recorded_FILTER_interior_control",
                    "registration": "../" + REGISTRATION,
                    "planned_actions": planned,
                }
            ),
        )
        write_bytes(
            directory / "instructions.md",
            (
                "# Recorded FILTER interior control\n\n"
                + "\n".join(f"{index}. {action}" for index, action in enumerate(planned, 1))
                + "\n\nDo not press keyboard keys or hold BPM/FX. Keep a quiet setting if it happens to be quiet; do not change the selected position to chase an audible result.\n"
            ).encode(),
        )
    print(json.dumps({"registered": True, "next_captures": list(CAPTURE_IDS)}))


if __name__ == "__main__":
    main()
