"""Register the polyphony test: how many sounds can play on one step?

Source: the verified parameter-only state. Fourteen sounds get distinct tones:
- melodic Sound1..8 already hold 0.5 s tones at 400 * 2^(150 (s-1) / 1200) Hz, which play
  7 semitones up at key 1;
- drum Sound13 and Sound14 hold 272 ms tones at 300 and 400 Hz on key 1;
- drum Sound11, 12, 15 and 16 are re-imported as kits of sixteen identical 272 ms tones at
  1500, 500, 1200 and 1350 Hz, keeping their 102400-code capacities.

Through the public plan path, after making Sound16's note parameters uniform (filter 63,
resonance 1, the template for every other sound):
- Pattern2 plays each of the fourteen sounds alone, one per step, on steps 1..14.
- Pattern3 stacks them on odd steps: 2, 4, 6, 8, 10 and 14 sounds, then all 14 again,
  then the 6 drum sounds alone.
- The chain becomes 2, 3.

Models registered before the session (frozen method scripts/polyphony_method.py, three
chain cycles): voice_limit_L for L in 2, 4, 6, 8, 10, 12 and 14 predicts that each stack
sounds min(requested, L) voices; 14 means at least 14, the largest stack. A model holds when every stack's majority count over
the cycles matches it.
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
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes, melodic_notes
from po33_re.modem.symbols import load_artifact
from po33_re.sample_import import DEVICE_SAMPLE_LIMIT
from scripts.polyphony_method import SETTINGS
from scripts.prepare_all_melodic_slots_test import TONE_HZ as MELODIC_HZ
from scripts.prepare_param_only_test import DIRECTORY as SOURCE_EXPERIMENT

TRANSPOSE = 2 ** (7 / 12)
REIMPORT_HZ = {11: 1500.0, 12: 500.0, 15: 1200.0, 16: 1350.0}
VOICES = {
    **{s: MELODIC_HZ[s] * TRANSPOSE for s in range(1, 9)},
    13: 300.0,
    14: 400.0,
    **REIMPORT_HZ,
}
SOUND_ORDER = [1, 2, 3, 4, 5, 6, 7, 8, 13, 14, 11, 12, 15, 16]
SOLO_PATTERN, STACK_PATTERN = 2, 3
CHAIN = [SOLO_PATTERN, STACK_PATTERN]
SOLO_STEPS = {sound: step for step, sound in enumerate(SOUND_ORDER, 1)}
STACKS = {
    1: [1, 2],
    3: [1, 2, 3, 4],
    5: [1, 2, 3, 4, 5, 6],
    7: [1, 2, 3, 4, 5, 6, 7, 8],
    9: [1, 2, 3, 4, 5, 6, 7, 8, 13, 14],
    11: SOUND_ORDER,
    13: SOUND_ORDER,
    15: [11, 12, 13, 14, 15, 16],
}
LIMITS = [2, 4, 6, 8, 10, 12, 14]  # 14 means at least 14: the largest stack
HIT_CODES, CAPACITY, LEVEL, FADE_SECONDS, WAV_RATE = 6375, 102400, 0.5, 0.003, 48000
HITS_DIRECTORY = "polyphony-hits-001"
PLAN_DIRECTORY = "polyphony-plan-001"
DIRECTORY = "compiled-polyphony-001"
REGISTRATION = "polyphony-registration-001.json"
PLAYBACK_SECONDS = 26
CYCLES = 3
QUESTION = "Did the second pattern's chords get thicker, and did any voices seem to drop out? (Enter to skip)"


def stage_name(slot):
    return f"import-drum{slot}-polyphony-stage-001"


def tone_wav(frequency):
    frames = HIT_CODES * 256 // 125
    t = np.arange(frames) / WAV_RATE
    tone = LEVEL * np.sin(2 * np.pi * frequency * t)
    fade = round(FADE_SECONDS * WAV_RATE)
    ramp = np.linspace(0, 1, fade)
    tone[:fade] *= ramp
    tone[-fade:] *= ramp[::-1]
    buffer = io.BytesIO()
    sf.write(buffer, tone, WAV_RATE, subtype="PCM_16", format="WAV")
    return buffer.getvalue()


def keys_for(pattern, sound):
    if pattern == SOLO_PATTERN:
        return [1 if SOLO_STEPS.get(sound) == step else None for step in range(1, 17)]
    return [1 if sound in STACKS.get(step, []) else None for step in range(1, 17)]


def note_operations(pattern):
    operations = []
    for sound in SOUND_ORDER:
        if sound == 16:
            continue
        operations.append(
            {
                "operation": "set_melodic_notes_from" if sound <= 8 else "set_drum_notes",
                "pattern": pattern,
                "sound": sound,
                "keys": keys_for(pattern, sound),
                "template_sound": 16,
            }
        )
    operations.append(
        {
            "operation": "set_drum_notes",
            "pattern": pattern,
            "sound": 16,
            "keys": keys_for(pattern, 16),
            "template_sound": 16,
        }
    )
    return operations


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    names = [HITS_DIRECTORY, PLAN_DIRECTORY, DIRECTORY, *map(stage_name, REIMPORT_HZ)]
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any((experiments / name).exists() for name in names):
        raise ValueError("Fresh folders and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or observation["classification"] != "param_only_sets_value"
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified parameter-only state is required")
    hits_folder = experiments / HITS_DIRECTORY
    hits_folder.mkdir()
    current, hits = source_path, {}
    for slot, frequency in REIMPORT_HZ.items():
        path = hits_folder / f"sound{slot}-{frequency:.0f}hz.wav"
        write_bytes(path, tone_wav(frequency))
        hits[slot] = path
        stage = experiments / stage_name(slot)
        compile_drum_kit_import(
            current,
            [path] * 16,
            stage,
            slot,
            capacity=CAPACITY,
            allowed_slots=(slot,),
            total_limit=DEVICE_SAMPLE_LIMIT,
        )
        current = stage / "edited.symbols.npz"
    stage_frame = decode_artifact(load_artifact(current))
    operations = []
    for pattern in CHAIN:
        notes = drum_notes(stage_frame, pattern, 16)
        for name, value in (("filter", 63), ("resonance", 1)):
            operations.append(
                {
                    "operation": "set_step_parameters",
                    "pattern": pattern,
                    "sound": 16,
                    "parameter": name,
                    "values": [value if key else None for key in notes],
                }
            )
        operations += note_operations(pattern)
    operations.append({"operation": "set_pattern_chain", "patterns": CHAIN})
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(current),
        "source_body_sha256": hashlib.sha256(stage_frame.encoded_body).hexdigest(),
        "operations": operations,
    }
    plan_folder = experiments / PLAN_DIRECTORY
    plan_folder.mkdir()
    plan_path = plan_folder / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    folder = experiments / DIRECTORY
    report = compile_edit_plan(current, plan_path, folder)
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    for pattern in CHAIN:
        for sound in SOUND_ORDER:
            reader = melodic_notes if sound <= 8 else drum_notes
            if reader(target, pattern, sound) != keys_for(pattern, sound):
                raise ValueError(f"Pattern{pattern} Sound{sound} is not as planned")
    if pattern_chain(target) != CHAIN:
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
                "import_stages": ["../" + stage_name(slot) for slot in REIMPORT_HZ],
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
                "analysis_version": "polyphony-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "voices_hz": {str(k): v for k, v in VOICES.items()},
                "solo_steps": {str(k): v for k, v in SOLO_STEPS.items()},
                "stacks": {str(k): v for k, v in STACKS.items()},
                "reimported_hits": {
                    str(slot): {"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p)}
                    for slot, p in hits.items()
                },
                "plan_sha256": sha256_file(plan_path),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "method_settings": SETTINGS,
                "method_script_sha256": sha256_file(root / "scripts/polyphony_method.py"),
                "models": {f"voice_limit_{L}": L for L in LIMITS},
                "cycles_measured": CYCLES,
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "A voice is present when its level is within 10 dB of its solo level in the same cycle",
                    "voice_limit_L holds when every stack's majority count over three cycles equals min(requested, L)",
                ],
                "limits": [
                    "Fourteen distinct sounds; Sound9 and Sound10, whose hits are 43 ms, are not stacked",
                    "Presence is judged 100 to 240 ms after the step, so voices that cut out later are not seen",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "voices": len(VOICES)}))


if __name__ == "__main__":
    main()
