"""Add retake-002 to the audition-lock observation: the volume knob raised first.

Retake-001 showed that after the restore, pressing key 1 by hand produced no output at
all, so the registered method had nothing to classify. The device still holds the
restored state. This retake raises the sound's live volume with knob B before the
recording, so the auditions become measurable, and then repeats the three-part
procedure. The question is unchanged: do the auditions after the pattern keep the live
setting (here, louder than the pattern's volume-36 locks) or take the pattern's locks?

The method, outcomes and prediction (audition_keeps_live_state) are those of the
registration; this file records the amended procedure before the recording.
"""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, write_bytes
from scripts.prepare_audition_lock_observation import DIRECTORY, PLAYBACK_SECONDS

INSTRUCTIONS = """One 32-second recording in three parts; do not press PLAY first. Before pressing Enter:

- Keep WRITE off and playback stopped.
- Select Sound 16: hold SOUND and press key 16.
- Turn knob B fully clockwise. Note what the screen calls it (expected: vol).
- Press key 1 once to confirm it is now audible. Keep every volume unchanged from here.

Press Enter, then within a second:

1. Press key 1 four times, about one second apart. These are the auditions before.
2. Wait about three seconds of silence. Press PLAY and let Pattern 1 play twice through
   (eight seconds; four hits per pass). Press PLAY to stop it.
3. Wait about three seconds of silence. Press key 1 four times, about one second apart.
   These are the auditions after.

The harness may warn that the level changed between parts; that is expected here, so
decline to record again unless a part was missed."""
QUESTIONS = [
    "What did the screen call knob B, and was key 1 audible after turning it? (Enter to skip)",
    "Did the auditions after the pattern sound as loud as the ones before, or quieter like the pattern? (Enter to skip)",
]


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    folder = Path(__file__).resolve().parents[1] / "experiments" / DIRECTORY
    retake = folder / "retake-002"
    retake.mkdir()
    write_bytes(
        retake / "experiment.json",
        json_bytes(
            {
                "experiment_id": f"{DIRECTORY}/retake-002",
                "kind": "playback_only_retake",
                "parent": "..",
                "reason": "Retake-001's auditions by hand produced no output; the live volume is raised with knob B before this recording so they can be measured",
                "registered_before_playback": True,
                "prediction": "audition_keeps_live_state",
                "expected_sign": "auditions before and after both louder than the pattern's hits by the same amount; the pattern's notes carry volume 36 locks",
                "playback_seconds": PLAYBACK_SECONDS,
                "playback_instructions": INSTRUCTIONS,
                "observation_questions": QUESTIONS,
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": retake.relative_to(folder.parent).as_posix()}))


if __name__ == "__main__":
    main()
