"""Register the first software drum-kit import: 16 WAV hits replace the Sound11 kit.

Source: the verified drum-notes state, where Pattern1 plays Sound11 key k on step k at
60 BPM and Sound11 holds the device's own recorded kit (102400-code buffer owned by id 40).

Sixteen 48 kHz mono WAVs are generated. Hit k is a tone at 1500 * 2^(-(k-1)/12) Hz lasting
exactly L_k = 1750 + 250 (k-1) native codes (74.7 to 234.7 ms), with 3 ms fades. The
importer concatenates them in key order into the same 102400-code buffer, with contiguous
windows, so total sample memory is unchanged.

Models, all registered before the session:
- Pitch per step, cents relative to step 1 (frozen grid method): new_kit_key_k predicts
  -100 (k-1); old_kit_still_playing predicts +150 (k-1).
- Absolute pitch of step 1 against 1500 Hz: stored_rate predicts 0 cents.
- Duration per step (frozen duration method): stops_at_window_end predicts L_k / 23437.5 s.
"""

import argparse
import io
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.drum_import import compile_drum_kit_import
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes
from po33_re.modem.symbols import load_artifact
from scripts.drum_slice_duration_method import SETTINGS as DURATION_SETTINGS
from scripts.prepare_drum_notes_writer_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.prepare_drum_notes_writer_test import SETTINGS

HITS_DIRECTORY = "drum-kit-hits-001"
DIRECTORY = "compiled-drum-kit-import-001"
REGISTRATION = "drum-kit-import-registration-001.json"
NATIVE_RATE = 23437.5
WAV_RATE, LEVEL, FADE_SECONDS = 48000, 0.5, 0.003
FREQUENCIES = [round(1500 * 2 ** (-(k - 1) / 12), 3) for k in range(1, 17)]
LENGTHS = [1750 + 250 * (k - 1) for k in range(1, 17)]
PLAYBACK_SECONDS = 22
QUESTION = "Did the pattern now play a falling run of 16 beeps that get longer? (Enter to skip)"
MODELS = {
    "new_kit_key_k": [-100.0 * (k - 1) for k in range(1, 17)],
    "old_kit_still_playing": [150.0 * (k - 1) for k in range(1, 17)],
}
ABSOLUTE_MODELS = {"stored_rate": 0.0}
DURATION_MODEL_MS = [length / NATIVE_RATE * 1000 for length in LENGTHS]


def hit_wav(frequency, native_length):
    frames = native_length * 256 // 125
    t = np.arange(frames) / WAV_RATE
    tone = LEVEL * np.sin(2 * np.pi * frequency * t)
    fade = round(FADE_SECONDS * WAV_RATE)
    ramp = np.linspace(0, 1, fade)
    tone[:fade] *= ramp
    tone[-fade:] *= ramp[::-1]
    buffer = io.BytesIO()
    sf.write(buffer, tone, WAV_RATE, subtype="PCM_16", format="WAV")
    return buffer.getvalue()


def absolute_decision(step1_hz):
    if step1_hz is None:
        return {"step1_cents_vs_hit1": None, "classification": "other_or_inconclusive"}
    cents = 1200 * math.log2(step1_hz / FREQUENCIES[0])
    close = [
        name
        for name, value in ABSOLUTE_MODELS.items()
        if abs(cents - value) <= SETTINGS["cents_tolerance"]
    ]
    return {
        "step1_cents_vs_hit1": cents,
        "classification": close[0] if close else "other_or_inconclusive",
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    hits_folder = root / "experiments" / HITS_DIRECTORY
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if registration_path.exists() or hits_folder.exists() or folder.exists():
        raise ValueError("Fresh folders and registration required")
    source_folder = root / "experiments" / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or observation["classification"] != "key_k_plays_slice_k"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified drum-notes state is required")
    if drum_notes(decode_artifact(load_artifact(source_path)), 1, 11) != list(range(1, 17)):
        raise ValueError("Pattern1 must play Sound11 keys 1..16 on steps 1..16")
    hits_folder.mkdir()
    paths = []
    for key, (frequency, length) in enumerate(zip(FREQUENCIES, LENGTHS, strict=True), 1):
        path = hits_folder / f"key{key:02d}-{frequency:.0f}hz-{length}codes.wav"
        write_bytes(path, hit_wav(frequency, length))
        paths.append(path)
    report = compile_drum_kit_import(source_path, paths, folder, 11)
    windows = report["allocation"]["windows"]
    if [end - start for start, end in windows] != LENGTHS:
        raise ValueError("Imported windows do not have the planned lengths")
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../" + REGISTRATION,
                "hits": "../" + HITS_DIRECTORY,
                "playback_seconds": PLAYBACK_SECONDS,
                "observation_questions": [QUESTION],
                "hardware_restore": {"status": "not_run"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "drum-kit-import-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "hits": [
                    {
                        "path": p.relative_to(root).as_posix(),
                        "sha256": sha256_file(p),
                        "hz": f,
                        "native_codes": n,
                    }
                    for p, f, n in zip(paths, FREQUENCIES, LENGTHS, strict=True)
                ],
                "import_report_sha256": sha256_file(folder / "import-report.json"),
                "allocation": report["allocation"],
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(
                    root / "scripts/pattern1_key_scale_grid_method.py"
                ),
                "models_cents": MODELS,
                "absolute_models_cents_vs_hit1": ABSOLUTE_MODELS,
                "duration_method_settings": DURATION_SETTINGS,
                "duration_method_script_sha256": sha256_file(
                    root / "scripts/drum_slice_duration_method.py"
                ),
                "duration_model_ms": DURATION_MODEL_MS,
                "decision": [
                    "The backup must equal the compiled target exactly, including every imported code and window",
                    "Pitch: a model holds when all 16 steps are within 20 cents of it in the five-loop median and in at least 4 of 5 loops",
                    "Absolute: step 1 within 20 cents of 1500 Hz",
                    "Duration: stops_at_window_end holds when all 16 steps are within 5 ms in the median and in at least 4 of 5 loops",
                ],
                "limits": [
                    "Replaces the kit in Sound11 only, with the observed 102400-code capacity; empty drum slots and other capacities are not tested",
                    "Pure tones with 3 ms fades; real drum hits are not played here",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "windows": windows[:3]}, indent=2))


if __name__ == "__main__":
    main()
