"""Exploratory re-read of the voice stealing playback with corrected long-note frequencies.

The registration predicted the key-13 notes one octave below key 1. The verified key
layout puts key 13 at 19 semitones below key 1, so Sound1 and Sound8 at key 13 play at
200.0 and 366.8 Hz, half the stored rate, for 1.0 s. The registered readings of those two
voices measured noise and are invalid; the other voices' readings stand. This script
re-reads every Pattern3 step at the corrected frequencies. Nothing here is registered.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.polyphony_method_exploratory import SETTINGS, presence, voice_levels
from scripts.prepare_polyphony_test import VOICES
from scripts.prepare_voice_steal_test import (
    CYCLES,
    DIRECTORY,
    SOLO_STEPS,
    VOICE_HZ,
    VOICE_NAMES,
)

EXPLORATORY = "voice-steal-exploratory-001.json"
KEY13_SEMITONES = -19
CORRECTED_HZ = {
    **VOICE_HZ,
    "1k13": VOICES[1] * 2 ** (KEY13_SEMITONES / 12),
    "8k13": VOICES[8] * 2 ** (KEY13_SEMITONES / 12),
}


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments" / DIRECTORY
    playback = folder / "playback.wav"
    output = root / "experiments" / EXPLORATORY
    validate_outputs([output], [playback], False)
    frequencies = [CORRECTED_HZ[name] for name in VOICE_NAMES]
    first, levels = voice_levels(playback, 32 * CYCLES, frequencies, SETTINGS)
    solo = {VOICE_NAMES.index(name): step for name, step in SOLO_STEPS.items()}
    cycles = presence(levels, solo, [16 + s for s in range(1, 17)], 32, SETTINGS)
    steps = {}
    for step in range(1, 17):
        rows = [c[16 + step] for c in cycles if c.get(16 + step) is not None]
        db = np.median([r["db_vs_solo"] for r in rows], axis=0)
        steps[step] = {
            "present": [VOICE_NAMES[i] for i, x in enumerate(db) if x >= SETTINGS["presence_db"]],
            "median_db_vs_solo": dict(zip(VOICE_NAMES, db.tolist(), strict=True)),
        }
    write_bytes(
        output,
        json_bytes(
            {
                "analysis_version": "voice-steal-exploratory-0.1",
                "hardware_verified": False,
                "exploratory": True,
                "playback_sha256": sha256_file(playback),
                "corrected_voice_hz": CORRECTED_HZ,
                "registration_error": "key 13 predicted as -12 semitones from key 1; the verified layout gives -19",
                "settings": SETTINGS,
                "first_onset_seconds": first,
                "steps": {str(k): v for k, v in steps.items()},
                "reading": "The long note survives every overflow; a fifth note plays when a sounding voice has 84 ms or less left (A, C) and is dropped when the only busy voice has 500 ms left (D)",
            }
        ),
    )
    print(json.dumps({str(k): v["present"] for k, v in steps.items()}))


if __name__ == "__main__":
    main()
