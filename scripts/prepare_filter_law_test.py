"""Register the filter law test: every filter code 0..62 against bypass code 63.

Known: code 63 is the audible bypass, 1 a full low-pass, 62 a full high-pass, 16 a partial
low-pass and 52 a partial high-pass (docs/sound3-filter-edits.md). The cutoff law is not.

Source: the verified drum-pitch state (Pattern1 plays Sound16 key 1 on every step).
1. Sound16 gets a kit of 16 identical hits: a 200 Hz sawtooth of 55 harmonics, 6375
   codes (272 ms), in the same 102400-code capacity, so total memory is unchanged.
2. Through the public plan path, Pattern1's Sound16 notes get pitch 13 and resonance 0;
   Pattern1 is copied to Patterns 2..5; each pattern's step 1 gets filter 63 (bypass)
   and steps 2..16 get the codes in FILTER_CODES; the chain becomes 1, 2, 3, 4, 5.

Hypotheses registered before the session (frozen method scripts/filter_response_method.py,
per code the median response over its occurrences in two chain cycles):
- reference_consistent: every bypass step is within 0.5 dB of its cycle reference
  (median over harmonics of the absolute response).
- low_codes_low_pass: codes 1..31 are low_pass, flat or silent; codes 1..16 low_pass or
  silent.
- high_codes_high_pass: codes 32..62 are high_pass, flat or silent; codes 47..62
  high_pass or silent.
- edges_monotonic: the -3 dB edge rises with the code among low_pass codes and among
  high_pass codes, allowing one harmonic (200 Hz) of reversal.
Code 0 is measured and reported only.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.drum_import import compile_drum_kit_import
from po33_re.edits import compile_edit_plan
from po33_re.formats.globals import pattern_chain
from po33_re.formats.notes import step_parameters
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes
from po33_re.modem.symbols import load_artifact
from po33_re.sample_import import DEVICE_SAMPLE_LIMIT
from scripts.filter_response_method import SETTINGS
from scripts.prepare_drum_pitch_test import DIRECTORY as SOURCE_EXPERIMENT

PATTERNS = [1, 2, 3, 4, 5]
FILTER_CODES = {p: [63, *range(15 * (p - 1), 15 * (p - 1) + 15)] for p in (1, 2, 3, 4)} | {
    5: [63, 60, 61, 62, 16, 52, 31, 32, 33, 30, 8, 24, 40, 56, 63, 63]
}
F0, HARMONICS, LEVEL, FADE_SECONDS, WAV_RATE = 200.0, 55, 0.5, 0.003, 48000
HIT_CODES, CAPACITY = 6375, 102400
HITS_DIRECTORY = "filter-law-hits-001"
STAGE = "import-drum16-filter-law-stage-001"
PLAN_DIRECTORY = "filter-law-plan-001"
DIRECTORY = "compiled-filter-law-001"
REGISTRATION = "filter-law-registration-001.json"
PLAYBACK_SECONDS = 44
QUESTION = (
    "Did one buzzy tone play, getting darker and then thinner across five patterns? (Enter to skip)"
)


def step_codes():
    """Filter code of every step of one chain cycle, in play order."""
    return [code for p in PATTERNS for code in FILTER_CODES[p]]


def saw_wav():
    frames = HIT_CODES * 256 // 125
    t = np.arange(frames) / WAV_RATE
    wave = sum(np.sin(2 * np.pi * h * F0 * t) / h for h in range(1, HARMONICS + 1))
    wave = LEVEL * wave / np.abs(wave).max()
    fade = round(FADE_SECONDS * WAV_RATE)
    ramp = np.linspace(0, 1, fade)
    wave[:fade] *= ramp
    wave[-fade:] *= ramp[::-1]
    buffer = io.BytesIO()
    sf.write(buffer, wave, WAV_RATE, subtype="PCM_16", format="WAV")
    return buffer.getvalue()


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    names = [HITS_DIRECTORY, STAGE, PLAN_DIRECTORY, DIRECTORY]
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any((experiments / name).exists() for name in names):
        raise ValueError("Fresh folders and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or observation["classification"] != "semitone_per_code"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified drum-pitch state is required")
    hits_folder = experiments / HITS_DIRECTORY
    hits_folder.mkdir()
    hit = hits_folder / "saw-200hz-55-harmonics.wav"
    write_bytes(hit, saw_wav())
    import_report = compile_drum_kit_import(
        source_path,
        [hit] * 16,
        experiments / STAGE,
        16,
        capacity=CAPACITY,
        allowed_slots=(16,),
        total_limit=DEVICE_SAMPLE_LIMIT,
    )
    stage = experiments / STAGE / "edited.symbols.npz"
    stage_frame = decode_artifact(load_artifact(stage))
    operations = [
        {
            "operation": "set_step_parameters",
            "pattern": 1,
            "sound": 16,
            "parameter": name,
            "values": [value] * 16,
        }
        for name, value in (("pitch", 13), ("resonance", 0))
    ]
    operations += [
        {"operation": "copy_pattern", "source_pattern": 1, "destination_pattern": p}
        for p in PATTERNS[1:]
    ]
    operations += [
        {
            "operation": "set_step_parameters",
            "pattern": p,
            "sound": 16,
            "parameter": "filter",
            "values": FILTER_CODES[p],
        }
        for p in PATTERNS
    ]
    operations.append({"operation": "set_pattern_chain", "patterns": PATTERNS})
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(stage),
        "source_body_sha256": hashlib.sha256(stage_frame.encoded_body).hexdigest(),
        "operations": operations,
    }
    plan_folder = experiments / PLAN_DIRECTORY
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    folder = experiments / DIRECTORY
    report = compile_edit_plan(stage, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    for p in PATTERNS:
        params = step_parameters(target, p, 16)
        if (
            drum_notes(target, p, 16) != [1] * 16
            or [s["filter"] for s in params] != FILTER_CODES[p]
            or {(s["pitch"], s["resonance"]) for s in params} != {(13, 0)}
        ):
            raise ValueError(f"Pattern{p} does not hold the planned notes")
    if pattern_chain(target) != PATTERNS:
        raise ValueError("Compiled target does not hold the planned chain")
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../" + REGISTRATION,
                "plan": "../" + PLAN_DIRECTORY + "/plan.json",
                "import_stages": ["../" + STAGE],
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
                "analysis_version": "filter-law-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "hit": {"path": hit.relative_to(root).as_posix(), "sha256": sha256_file(hit)},
                "allocation": import_report["allocation"],
                "filter_codes_by_pattern": {str(k): v for k, v in FILTER_CODES.items()},
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/filter_response_method.py"),
                "hypotheses": {
                    "reference_consistent": "every bypass step within 0.5 dB of its cycle reference (median over harmonics of |response|)",
                    "low_codes_low_pass": "codes 1..31 low_pass, flat or silent; 1..16 low_pass or silent",
                    "high_codes_high_pass": "codes 32..62 high_pass, flat or silent; 47..62 high_pass or silent",
                    "edges_monotonic": "the -3 dB edge rises with the code within each type, allowing 200 Hz reversal",
                },
                "cycles_measured": 2,
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "Each hypothesis is evaluated on per-code median responses over all occurrences in two chain cycles",
                ],
                "limits": [
                    "Resonance 0, pitch 13, volume 36 and one 200 Hz sawtooth; harmonics up to 10 kHz",
                    "The response includes the PO-33 output stage, cancelled by the bypass reference",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "steps_per_cycle": len(step_codes())}))


if __name__ == "__main__":
    main()
