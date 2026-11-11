"""Shrink the drum kits so restores and backups transfer faster.

Transfer time grows with the sample data in a backup. The tests since the filter law
only play key 1 of each drum kit, so each kit is re-imported with its key-1 tone unchanged
and keys 2..16 as 20 ms of silence, the shortest hit the importer accepts. A kit then
takes 4 pages instead of 25. The key-1 tones are regenerated from the same parameters the
earlier tests used, so they are identical to the ones on the device.
"""

import io

import numpy as np
import soundfile as sf

from po33_re.artifacts import write_bytes
from po33_re.drum_import import SLICE_FRAMES, compile_drum_kit_import
from po33_re.sample_import import DEVICE_SAMPLE_LIMIT
from scripts.prepare_drum_kit_import_test import hit_wav
from scripts.prepare_polyphony_test import REIMPORT_HZ

# slot -> (frequency, native codes) of the key-1 tone every current test relies on.
KEY1_TONES = {
    9: (300.0, 1000),
    10: (300.0, 1000),
    11: (REIMPORT_HZ[11], 6375),
    12: (REIMPORT_HZ[12], 6375),
    13: (300.0, 6375),
    14: (400.0, 6375),
    15: (REIMPORT_HZ[15], 6375),
    16: (REIMPORT_HZ[16], 6375),
}


def silence_wav(native_codes=SLICE_FRAMES[0]):
    frames = native_codes * 256 // 125
    buffer = io.BytesIO()
    sf.write(buffer, np.zeros(frames), 48000, subtype="PCM_16", format="WAV")
    return buffer.getvalue()


def key1_wav(slot):
    frequency, codes = KEY1_TONES[slot]
    return hit_wav(frequency, codes)


def slim_drum_kits(source_path, experiments, prefix, slots=tuple(KEY1_TONES)):
    """Re-import each kit slim; return the final artifact path and the per-slot reports."""
    hits_folder = experiments / f"{prefix}-slim-hits-001"
    hits_folder.mkdir()
    silence = hits_folder / "silence-20ms.wav"
    write_bytes(silence, silence_wav())
    current, reports = source_path, {}
    for slot in slots:
        tone = hits_folder / f"sound{slot}-key1.wav"
        write_bytes(tone, key1_wav(slot))
        stage = experiments / f"import-drum{slot}-{prefix}-slim-stage-001"
        reports[slot] = compile_drum_kit_import(
            current,
            [tone] + [silence] * 15,
            stage,
            slot,
            allowed_slots=(slot,),
            total_limit=DEVICE_SAMPLE_LIMIT,
        )
        current = stage / "edited.symbols.npz"
    return current, reports
