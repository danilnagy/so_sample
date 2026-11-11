"""Register the aux-nibble test: note length and drum retrigger in a step's auxiliary nibble.

The restore in experiments/aux-nibble-001 was built by web/scripts/build-aux-nibble-test.ts
(docs/aux-nibble-control.md): at 60 BPM, a 12 ms click on Sound 9 key 1 with auxiliary high
nibbles 1, 2, 3, 4, 6, 8, 5 and 7 (eight steps apart, Patterns 1 to 4), and a 3 s 500 Hz tone
on Sound 1 key 5 with nibbles F, 1, 2, 4, 8 and E (one per pattern, Patterns 5 to 10).

This script decodes the TypeScript restore with the Python decoder into the expected
artifact, requires its packets to equal the compiler's packets.json, pins the frozen
measurement method (scripts/aux_nibble_method.py) by hash, and writes the experiment record
and the registration with the predictions, before any data is taken.
"""

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.globals import pattern_chain, swing, tempo
from po33_re.formats.packets import Packet, decode_artifact, encode_packets
from po33_re.modem.symbols import load_artifact
from scripts.aux_nibble_method import SETTINGS

DIRECTORY = "aux-nibble-001"
REGISTRATION = "aux-nibble-registration-001.json"
METHOD = "scripts/aux_nibble_method.py"
# Two full passes of the 40 s chain, and a margin for pressing PLAY.
PLAYBACK_SECONDS = 90
STEP = SETTINGS["step_seconds"]
TONE_SECONDS = 3.0

# The predictions, registered before the session. Drum: own-step onsets per nibble. Melodic:
# sounding duration per nibble (hex), in seconds.
PREDICTIONS = {
    "H1_drum_retrigger": {
        "kind": "drum_onsets",
        "statement": "A drum step with high nibble n in 1, 2, 3, 4, 6, 8 plays n onsets within its own step (the retrigger counts the device's interface cycles through)",
        "expected": {"1": 1, "2": 2, "3": 3, "4": 4, "6": 6, "8": 8},
    },
    "H0_drum_no_effect": {
        "kind": "drum_onsets",
        "statement": "The nibble has no audible effect on a drum step: every probe plays one onset in its step, as stray-bits-results.md would suggest",
        "expected": {"1": 1, "2": 1, "3": 1, "4": 1, "6": 1, "8": 1, "5": 1, "7": 1},
    },
    "H1_melodic_length": {
        "kind": "melodic_duration",
        "statement": "A melodic note with high nibble n in 1, 2, 4, 8 sounds for n steps (250 ms each, within 60 ms); F and E sound the whole 3 s tone, being longer than it",
        "expected_seconds": {"1": STEP, "2": 2 * STEP, "4": 4 * STEP, "8": 8 * STEP, "F": TONE_SECONDS, "E": TONE_SECONDS},
        "tolerance_seconds": 0.06,
    },
    "H0_melodic_no_effect": {
        "kind": "melodic_duration",
        "statement": "The nibble has no audible effect on a melodic note: every probe sounds the whole 3 s tone (within 100 ms), as stray-bits-results.md found for nibbles 2 and E",
        "expected_seconds": {k: TONE_SECONDS for k in ("F", "1", "2", "4", "8", "E")},
        "tolerance_seconds": 0.1,
    },
}

QUESTIONS = [
    "Patterns 1 to 4 (clicks): did some steps play a quick burst of repeated clicks rather than one? Roughly how many? (notes)",
    "Patterns 5 to 10 (a steady tone, one per bar): did some tones stop short of the others? (notes)",
    "Did the device show ERR, or anything unusual on its screen? (yes/no/notes)",
    "Anything else you noticed (Enter to skip)",
]
INSTRUCTIONS = """# Aux-nibble test

After the restore, press PLAY and let the chain run: ten one-bar patterns at 60 BPM (four
seconds each, 40 s a pass). Keep the volume where you set it, and do not touch any knob or
button while it plays; the recording should hold two full passes.

- Patterns 1 to 4: a short click on steps 1 and 9 of each bar. Some steps may play a burst
  of repeated clicks instead of one; that is what this test measures.
- Patterns 5 to 10: a steady 500 Hz tone starting on step 1 of each bar. Some may stop
  early; that is what this test measures.
"""


def load_packets(path):
    view = json.loads(path.read_text())
    if view.get("schema") != "sosample.packets":
        raise ValueError("Expected a sosample packets file")
    return tuple(Packet(p["tag"], base64.b64decode(p["payload"])) for p in view["packets"])


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    for required in ("restore.wav", "packets.json", "project.json"):
        if not (folder / required).exists():
            raise ValueError(f"Run web/scripts/build-aux-nibble-test.ts first; missing {required}")
    if registration_path.exists() or (folder / "edited.symbols.npz").exists():
        raise ValueError("Fresh registration required")
    project = json.loads((folder / "project.json").read_text())
    if project["step_seconds"] != STEP or project["tone"]["seconds"] != TONE_SECONDS:
        raise ValueError("The built restore does not match the registered timing")
    if len(project["chain"]) != SETTINGS["chain_patterns"]:
        raise ValueError("The built chain does not match the frozen method")
    packets = load_packets(folder / "packets.json")
    target_path = folder / "edited.symbols.npz"
    subprocess.run(
        [sys.executable, "-m", "po33_re", "decode", str(folder / "restore.wav"), "--out", str(target_path)],
        cwd=root,
        check=True,
        capture_output=True,
    )
    target = decode_artifact(load_artifact(target_path))
    if target.packets != packets or encode_packets(packets) != target.encoded_body:
        target_path.unlink()
        raise ValueError("The decoded restore does not carry the TypeScript packets")
    write_bytes(folder / "instructions.md", INSTRUCTIONS.encode())
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../" + REGISTRATION,
                "builder": "web/scripts/build-aux-nibble-test.ts",
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
                "analysis_version": "aux-nibble-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "expected_artifact_source": "Python decode of the TypeScript restore.wav",
                "packets_json_sha256": sha256_file(folder / "packets.json"),
                "project_json_sha256": sha256_file(folder / "project.json"),
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "edited_artifact_sha256": sha256_file(target_path),
                "restore_wav_sha256": sha256_file(folder / "restore.wav"),
                "decoded_restore_carries_typescript_packets": True,
                "tempo": tempo(target),
                "swing": swing(target),
                "chain": pattern_chain(target),
                "drum_probes": project["drum_probes"],
                "melodic_probes": project["melodic_probes"],
                "aux_bytes": project["aux_bytes"],
                "tone_seconds": TONE_SECONDS,
                "method_script": METHOD,
                "method_script_sha256": sha256_file(root / METHOD),
                "method_settings": SETTINGS,
                "playback_seconds": PLAYBACK_SECONDS,
                "predictions": {
                    "reception": "The backup equals the compiled target exactly (every packet and the whole body), raw auxiliary bytes included",
                    **PREDICTIONS,
                },
                "decision": [
                    "Exact reception is decided by the native check of the backup against the target",
                    "Each audible prediction is decided by the frozen method on playback.wav, by majority over the full passes recorded",
                    "H1 and H0 exclude each other per sound; if neither holds for a sound, the result is recorded as neither, with the measurements, and no rule is adopted",
                    "Drum nibbles 5 and 7 are outside the interface's cycle: their counts are reported as exploratory and decide nothing except under H0",
                    "Window onset counts (all eight steps after a drum probe) and the user's answers are exploratory",
                ],
                "limits": [
                    "One session on one device",
                    "Onset counting assumes repeats are separated by at least 12 ms; a retrigger faster than that would be undercounted",
                    "A length unit other than one step would fail H1 and show in the measured durations",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "packets": len(packets)}))


if __name__ == "__main__":
    main()
