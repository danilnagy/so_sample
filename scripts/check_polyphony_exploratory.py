"""Exploratory polyphony reading after the frozen method failed to run.

Records the registered method's failure in the decision file, then analyses the playback
with the exploratory method variant. Nothing here is a registered result.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_polyphony_test import CYCLE_STEPS, DECISION, evaluate
from scripts.polyphony_method import SETTINGS as FROZEN_SETTINGS
from scripts.polyphony_method import voice_levels as frozen_voice_levels
from scripts.polyphony_method_exploratory import SETTINGS, presence, voice_levels
from scripts.prepare_polyphony_test import (
    CYCLES,
    DIRECTORY,
    REGISTRATION,
    SOLO_STEPS,
    SOUND_ORDER,
    STACKS,
    VOICES,
)

EXPLORATORY = "polyphony-exploratory-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments" / DIRECTORY
    playback = folder / "playback.wav"
    native_path = folder / "hardware-recapture-results-001.json"
    decision_path = root / "experiments" / DECISION
    exploratory_path = root / "experiments" / EXPLORATORY
    validate_outputs([decision_path, exploratory_path], [playback, native_path], False)
    frequencies = [VOICES[s] for s in SOUND_ORDER]
    try:
        frozen_voice_levels(playback, CYCLE_STEPS * CYCLES, frequencies, FROZEN_SETTINGS)
        raise ValueError("The frozen method ran; use the registered check instead")
    except ValueError as exc:
        failure = str(exc)
    write_bytes(
        decision_path,
        json_bytes(
            {
                "analysis_version": "polyphony-decision-0.1",
                "hardware_verified": False,
                "registration_sha256": sha256_file(root / "experiments" / REGISTRATION),
                "native_results_sha256": sha256_file(native_path),
                "classification": "method_failed_to_run",
                "frozen_method_error": failure,
                "exploratory_analysis": EXPLORATORY,
            }
        ),
    )
    first, levels = voice_levels(playback, CYCLE_STEPS * CYCLES, frequencies, SETTINGS)
    solo = {SOUND_ORDER.index(s): step for s, step in SOLO_STEPS.items()}
    cycles = presence(levels, solo, [16 + s for s in STACKS], CYCLE_STEPS, SETTINGS)
    result = evaluate(cycles)
    write_bytes(
        exploratory_path,
        json_bytes(
            {
                "analysis_version": "polyphony-exploratory-0.1",
                "hardware_verified": False,
                "exploratory": True,
                "playback_sha256": sha256_file(playback),
                "settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/polyphony_method_exploratory.py"
                ),
                "first_onset_seconds": first,
                "sound_order": SOUND_ORDER,
                "step_levels": [None if np.isnan(row).any() else row.tolist() for row in levels],
                **result,
            }
        ),
    )
    print(
        json.dumps(
            {
                "frozen_method_error": failure,
                "exploratory_classification": result["classification"],
                "counts": {
                    k: None if v is None else [len(v["requested"]), v["count"], v["unexpected"]]
                    for k, v in result["stacks"].items()
                },
            }
        )
    )


if __name__ == "__main__":
    main()
