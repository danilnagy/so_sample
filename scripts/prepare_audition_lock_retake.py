"""Add a playback-only retake folder to the audition-lock observation.

The first session's playback held the pattern alone: the procedure was shown at the
restore step, so PLAY ran for the whole recording. The device still holds the restored
state and the pattern has played once, so the three-part recording can be taken again
without a new restore, in a numbered retake folder under the experiment. The registered
restore, target, method and prediction are unchanged; the check reads the newest retake.

Because the pattern has already played, the retake's "before" auditions come after one
pattern play. If they match the pattern, the outcome cannot separate "locks were
followed" from "the live setting was the bypass all along" and a rerun with the filter
knob turned down is needed; if they differ from the pattern, the registered outcomes
still apply.
"""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, write_bytes
from scripts.prepare_audition_lock_observation import DIRECTORY, INSTRUCTIONS, PLAYBACK_SECONDS


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    folder = Path(__file__).resolve().parents[1] / "experiments" / DIRECTORY
    number = 1 + len(list(folder.glob("retake-*")))
    retake = folder / f"retake-{number:03d}"
    retake.mkdir()
    write_bytes(
        retake / "experiment.json",
        json_bytes(
            {
                "experiment_id": f"{DIRECTORY}/retake-{number:03d}",
                "kind": "playback_only_retake",
                "parent": "..",
                "reason": "The first playback held the pattern alone; the procedure is repeated without a new restore",
                "playback_seconds": PLAYBACK_SECONDS,
                "playback_instructions": INSTRUCTIONS,
            }
        ),
    )
    print(
        json.dumps(
            {
                "ready": True,
                "folder": retake.relative_to(folder.parent).as_posix(),
                "seconds": PLAYBACK_SECONDS,
            }
        )
    )


if __name__ == "__main__":
    main()
