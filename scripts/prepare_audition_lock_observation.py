"""Register the audition-lock observation: do auditions follow a pattern's locks?

A backup stores no base knob settings (docs/sound-knobs-results.md); every note the web
app writes carries full locks, so patterns play as designed, but auditioning a sound by
hand after a restore plays at whatever the device holds. The person reported, with the
filter apparently closed on auditions, that playing the pattern once did not change it.
This observation measures that with one recording.

The restore is built by the web app's own compiler (web/scripts/build-audition-lock-
restore.ts): Sound 16 key 1 holds a 200 Hz sawtooth hit, and Pattern 1 plays it on steps
1, 5, 9 and 13 with the app's default locks, filter 63 (the bypass) among them. One
32-second playback recording holds four auditions by hand, two passes of the pattern,
and four auditions by hand again. The frozen method in scripts/audition_lock_method.py
compares the three groups.

Registered before the session: the prediction is audition_keeps_live_state, from the
person's informal report; the alternatives are listed with it.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from scripts.audition_lock_method import OUTCOMES, SETTINGS

DIRECTORY = "observe-audition-locks-001"
REGISTRATION = "audition-lock-registration-001.json"
PLAYBACK_SECONDS = 32
PREDICTION = "audition_keeps_live_state"
QUESTIONS = [
    "Did the four auditions before the pattern sound duller or quieter than the pattern's hits? (Enter to skip)",
    "Did the four auditions after the pattern sound like the ones before, or like the pattern? (Enter to skip)",
    "Anything else you noticed? (Enter to skip)",
]
INSTRUCTIONS = """One 32-second recording in three parts; do not press PLAY first. Before pressing Enter:

- Keep WRITE off and playback stopped. Do not touch knobs A or B at any point.
- Select Sound 16: hold SOUND and press key 16. Keep every volume unchanged.

Press Enter, then within a second:

1. Press key 1 four times, about one second apart. These are the auditions before.
2. Wait about three seconds of silence. Press PLAY and let Pattern 1 play twice through
   (eight seconds; four hits per pass). Press PLAY to stop it.
3. Wait about three seconds of silence. Press key 1 four times, about one second apart.
   These are the auditions after.

The harness may warn that the level changed between parts; that is expected here, so
decline to record again unless a part was missed."""


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    folder = experiments / DIRECTORY
    registration_path = experiments / REGISTRATION
    if folder.exists() or registration_path.exists():
        raise ValueError("Fresh folder and registration required")
    folder.mkdir()
    built = subprocess.run(
        ["npx", "tsx", "scripts/build-audition-lock-restore.ts", str(folder)],
        cwd=root / "web",
        check=True,
        capture_output=True,
        text=True,
    )
    build = json.loads(built.stdout.strip().splitlines()[-1])
    target = folder / "edited.symbols.npz"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "po33_re",
            "decode",
            str(folder / "restore.wav"),
            "--out",
            str(target),
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "kind": "playback_observation_after_restore",
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../" + REGISTRATION,
                "playback_seconds": PLAYBACK_SECONDS,
                "playback_instructions": INSTRUCTIONS,
                "observation_questions": QUESTIONS,
                "hardware_restore": {"status": "not_run"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "audition-lock-registration-0.1",
                "hardware_verified": False,
                "registered_before_playback": True,
                "experiment_id": DIRECTORY,
                "restore_wav_sha256": sha256_file(folder / "restore.wav"),
                "edited_artifact_sha256": sha256_file(target),
                "build": build,
                "build_script": "web/scripts/build-audition-lock-restore.ts",
                "build_script_sha256": sha256_file(
                    root / "web/scripts/build-audition-lock-restore.ts"
                ),
                "method_script": "scripts/audition_lock_method.py",
                "method_script_sha256": sha256_file(root / "scripts/audition_lock_method.py"),
                "method_settings": SETTINGS,
                "playback_seconds": PLAYBACK_SECONDS,
                "instructions": INSTRUCTIONS,
                "outcomes": OUTCOMES,
                "prediction": PREDICTION,
                "prediction_basis": "The person reported on 2026-11-07 that after a restore the auditions sounded as if the filter were closed, and that playing the pattern did not change that. Exploratory, not measured.",
                "limits": [
                    "One device, one sound, one key; the live knob setting is whatever the device holds and is not controlled",
                    "If the live setting already is the bypass, the groups cannot be told apart; a rerun with the filter knob turned fully counterclockwise before the auditions is then planned",
                    "Hand-pressed auditions are timed by the person; the method needs three groups separated by over two seconds",
                ],
            }
        ),
    )
    print(
        json.dumps(
            {"ready": True, "folder": DIRECTORY, "restore_wav_sha256": build["restore_wav_sha256"]}
        )
    )


if __name__ == "__main__":
    main()
