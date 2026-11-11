"""Register the project build test: a small song assembled from a description.

This is the first end-to-end use of the toolkit as an editor would use it: a project
spec (samples, patterns, chain, tempo, swing) goes through po33_re.project_build, which
imports the samples and compiles one edit plan with the verified writers.

Source: the verified priority-map state. The spec:
- Sound8: a new 0.3 s tone at 523.25 Hz (C5), played by a melody of keys 1, 3, 5 and 8.
- Sound9: a new kit of sixteen 85 ms tones at 500 * 2^((k-1)/12) Hz.
- Pattern1: melody on odd steps, Sound13 (300 Hz) on steps 1, 5, 9, 13, Sound14 (400 Hz) on
  5 and 13, Sound9 key 1 on steps 2, 6, 10, 14.
- Pattern2: the melody transposed by keys, with filter 24 and resonance 40 on its notes,
  a filter lock on an empty step, the same drums, and FX 7 on step 16.
- Chain 1, 2, 2, 1; tempo 100; swing 4.

Models registered before the session (frozen methods: swing_onset_method for onsets,
polyphony_method_exploratory for levels):
- exact reception of the whole build;
- tempo_100: Sound13 onsets (250 to 350 Hz band) are 0.600 s apart, within 5 ms;
- swing_4: each Sound9 key-1 onset (450 to 550 Hz band) follows the Sound13 onset before
  it by 0.150 * (1 + 4/24) = 0.175 s, within 5 ms;
- melody_first_note: Sound8 at key 1 (784.0 Hz) sounds in step 1 and not in step 2, by at
  least 20 dB.
"""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.globals import pattern_chain, swing, tempo
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes, melodic_notes
from po33_re.modem.symbols import load_artifact
from po33_re.project_build import build_project
from scripts.polyphony_method_exploratory import SETTINGS as LEVEL_BASE
from scripts.prepare_drum_kit_import_test import hit_wav
from scripts.prepare_priority_map_test import DIRECTORY as SOURCE_EXPERIMENT
from scripts.swing_onset_method import SETTINGS as ONSET_BASE

TEMPO, SWING, CHAIN = 100, 4, [1, 2, 2, 1]
STEP_SECONDS = 60 / TEMPO / 4
MELODY_HZ, MELODY_CODES = 523.25, 7031
KIT_BASE_HZ, KIT_CODES = 500.0, 2000
MELODY_1 = [1, None, 3, None, 5, None, 8, None, 1, None, 3, None, 5, None, 8, None]
MELODY_2 = [5, None, 8, None, 1, None, 3, None, 5, None, 8, None, 1, None, 3, None]
KICK = [1 if s in (1, 5, 9, 13) else None for s in range(1, 17)]
SNARE = [1 if s in (5, 13) else None for s in range(1, 17)]
HAT = [1 if s in (2, 6, 10, 14) else None for s in range(1, 17)]
SPEC = {
    "tempo": TEMPO,
    "swing": SWING,
    "chain": CHAIN,
    "melodic": {"8": "experiments/project-build-source-001/melody-c5.wav"},
    "drums": {
        "9": [f"experiments/project-build-source-001/kit-key{k:02d}.wav" for k in range(1, 17)]
    },
    "patterns": {
        "1": {"notes": {"8": MELODY_1, "13": KICK, "14": SNARE, "9": HAT}},
        "2": {
            "notes": {"8": MELODY_2, "13": KICK, "14": SNARE, "9": HAT},
            "parameters": {"8": {"filter": 24, "resonance": 40}},
            "locks": {"8": {"filter": [None, 40] + [None] * 14}},
            "effects": [None] * 15 + [7],
        },
    },
}
ONSET_KICK = {**ONSET_BASE, "band_hz": [250.0, 350.0], "steps_per_loop": 4, "loops": 10}
ONSET_HAT = {**ONSET_BASE, "band_hz": [450.0, 550.0], "steps_per_loop": 4, "loops": 10}
LEVEL_SETTINGS = {**LEVEL_BASE, "step_seconds": STEP_SECONDS, "window_ms": [100.0, 190.0]}
MELODY_KEY1_HZ = MELODY_HZ * 2 ** (7 / 12)
EXPECTED = {"kick_interval_s": 4 * STEP_SECONDS, "hat_offset_s": STEP_SECONDS * (1 + SWING / 24)}
TOLERANCES = {"seconds": 0.005, "melody_db": 20.0}
SOURCE_DIRECTORY = "project-build-source-001"
BUILD_DIRECTORY = "project-build-001"
DIRECTORY = "project-build-001/compiled"
REGISTRATION = "project-build-registration-001.json"
PLAYBACK_SECONDS = 24
QUESTION = "Did it play like a small beat with a melody, and did the second half sound filtered? (Enter to skip)"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any(
        (experiments / name).exists() for name in (SOURCE_DIRECTORY, BUILD_DIRECTORY)
    ):
        raise ValueError("Fresh folders and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or not observation["checks"]["session_target_exact"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified priority-map state is required")
    sources = experiments / SOURCE_DIRECTORY
    sources.mkdir()
    write_bytes(sources / "melody-c5.wav", hit_wav(MELODY_HZ, MELODY_CODES))
    for k in range(1, 17):
        write_bytes(
            sources / f"kit-key{k:02d}.wav", hit_wav(KIT_BASE_HZ * 2 ** ((k - 1) / 12), KIT_CODES)
        )
    report = build_project(source_path, SPEC, experiments / BUILD_DIRECTORY)
    if not report["passed"]:
        raise ValueError("Project build failed its software checks")
    folder = experiments / DIRECTORY
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    checks = [
        melodic_notes(target, 1, 8) == MELODY_1,
        melodic_notes(target, 2, 8) == MELODY_2,
        drum_notes(target, 1, 13) == KICK,
        drum_notes(target, 2, 9) == HAT,
        pattern_chain(target) == CHAIN,
        tempo(target) == TEMPO,
        swing(target) == SWING,
    ]
    if not all(checks):
        raise ValueError(f"Compiled target is not as planned: {checks}")
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../../" + REGISTRATION,
                "build_report": "../build-report.json",
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
                "analysis_version": "project-build-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "spec": SPEC,
                "spec_sha256": report["spec_sha256"],
                "build_report_sha256": sha256_file(
                    experiments / BUILD_DIRECTORY / "build-report.json"
                ),
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "onset_settings": {"kick": ONSET_KICK, "hat": ONSET_HAT},
                "onset_method_script_sha256": sha256_file(root / "scripts/swing_onset_method.py"),
                "level_settings": LEVEL_SETTINGS,
                "level_method_script_sha256": sha256_file(
                    root / "scripts/polyphony_method_exploratory.py"
                ),
                "expected": EXPECTED,
                "melody_key1_hz": MELODY_KEY1_HZ,
                "tolerances": TOLERANCES,
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "tempo_100: median Sound13 onset interval within 5 ms of 0.600 s",
                    "swing_4: median Sound9 onset offset from the preceding Sound13 onset within 5 ms of 0.175 s",
                    "melody_first_note: 784 Hz level in step 1 exceeds step 2 by at least 20 dB",
                ],
                "limits": [
                    "One small project; the builder's software checks, not this test, cover other specs",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "expected": EXPECTED}))


if __name__ == "__main__":
    main()
