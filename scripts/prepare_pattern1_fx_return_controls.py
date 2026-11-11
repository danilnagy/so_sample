"""Register FX8 and FX16 with explicit footer/global alternatives after FX7's strict failure."""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes

CAPTURE_IDS = ("event-066-b-pattern1-FX8-recorded", "event-067-c-pattern1-FX16-clear")
REGISTRATION = "pattern1-FX8-clear-return-registration-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/event-065-a-pattern1-FX7-recorded"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    previous = json.loads(
        (root / "experiments/pattern1-FX7-probe-registration-001.json").read_text()
    )
    if (
        not observation["hardware_verified"]
        or not all(observation["checks"].values())
        or sha256_file(root / observation["artifact_path"]) != observation["artifact_sha256"]
        or sha256_file(folder / "capture.wav") != observation["capture_sha256"]
    ):
        raise ValueError("Verified literal FX7 footer/global observation required")
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    registration_path = root / "experiments" / REGISTRATION
    if registration_path.exists() or any(
        path.exists() or path.is_symlink() for path in directories
    ):
        raise ValueError("Fresh FX8/clear registration and both folders required")
    baseline = root / previous["source_artifact"]
    if sha256_file(baseline) != previous["source_artifact_sha256"]:
        raise ValueError("Independent original no-FX artifact changed")
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "FX8-and-clear-footer-global-return-preregistration-0.1",
                "hardware_verified": False,
                "registered_before_both_captures": True,
                "scope_revised_after_FX7_observation": True,
                "source_artifact": observation["artifact_path"],
                "source_artifact_sha256": observation["artifact_sha256"],
                "source_capture": (folder / "capture.wav").relative_to(root).as_posix(),
                "source_capture_sha256": observation["capture_sha256"],
                "source_body_sha256": observation["body_sha256"],
                "source_observation_sha256": sha256_file(observation_path),
                "independent_no_FX_artifact": previous["source_artifact"],
                "independent_no_FX_artifact_sha256": previous["source_artifact_sha256"],
                "independent_no_FX_body_sha256": previous["source_body_sha256"],
                "expected_packet_count": 815,
                "expected_frame_end_byte": 156758,
                "footer_candidate": previous["footer_candidate"],
                "global_candidate": {
                    "packet_index": 2,
                    "tag": 32092,
                    "payload_offset": 131,
                    "narrow_mask": 15,
                    "broader_mask": 255,
                },
                "expected_capture_sequence": [
                    {
                        "experiment_id": CAPTURE_IDS[0],
                        "official_effect_key": 8,
                        "official_effect_name": "octave_down",
                        "expected_footer_hex": "77" * 8,
                        "raw_code_model": "New key-minus-one mapping hypothesis predicts7 after observed FX7 code6",
                        "expected_global_byte": None,
                    },
                    {
                        "experiment_id": CAPTURE_IDS[1],
                        "official_effect_key": 16,
                        "official_effect_name": "no_effect_clear",
                        "expected_footer_hex": "ff" * 8,
                        "expected_global_byte": None,
                    },
                ],
                "official_control_source": "https://teenage.engineering/guides/po-33/en",
                "limits": [
                    "Original footer-only FX7 prediction failed due to global byte131 0-to9; original report remains immutable; footer-plus-global masks are new hypotheses registered before these captures",
                    "Global byte131 meaning and both new values are unknown; low-four and whole-byte scopes remain separate, with all other fields exact",
                    "FX8 raw7 and clear raw15 are new footer hypotheses, not pre-existing full effect-map facts; failures/mixed values remain literal without averaging",
                    "Clear should match the independent no-FX state except the explicitly unknown global byte131; full original-body equality is an additional diagnostic, not a guessed global-byte target",
                    "Nibble order remains unresolved for uniform vectors; no exact whole FX8 body, public FX writer or full map is predicted",
                ],
            }
        ),
    )
    for directory, key in zip(directories, (8, 16)):
        directory.mkdir()
        actions = [
            "Keep Pattern1 selected, both knobs and recording settings unchanged; stop playback",
            "Press WRITE once to enable write mode and confirm its indicator; leave WRITE released",
            f"Start playback and hold FX plus key{key} together for about8 seconds",
            "Release FX/key, immediately stop playback, then switch write mode off",
            "Save full capture.wav here at established reduced level with one second trailing silence before proceeding; report actual audible changes",
            "No restore, knob adjustment or separate playback.wav is needed",
        ]
        write_bytes(
            directory / "experiment.json",
            json_bytes(
                {
                    "experiment_id": directory.name,
                    "capture_status": "awaiting_recorded_FX8_clear_control",
                    "registration": "../" + REGISTRATION,
                    "planned_actions": actions,
                }
            ),
        )
        write_bytes(
            directory / "instructions.md",
            (
                "# Saved FX control\n\n"
                + "\n".join(f"{index}. {action}" for index, action in enumerate(actions, 1))
                + "\n"
            ).encode(),
        )
    print(
        json.dumps(
            {
                "registered": True,
                "next_captures": list(CAPTURE_IDS),
                "both_global_values_unknown": True,
            }
        )
    )


if __name__ == "__main__":
    main()
