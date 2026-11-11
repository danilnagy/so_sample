"""Register the aux-nibble-002 test: retrigger voices and choke, the remaining melodic lengths.

The restore in experiments/aux-nibble-002 was built by web/scripts/build-aux-nibble-2-test.ts
(docs/aux-nibble-2-control.md), at 60 BPM with no swing:

- Pattern 1: the drum (Sound 9 key 1: a 7 kHz click onset and a 1 s noise body around
  3 kHz) once as a single hit (step 1, nibble 1) and once retriggered 4 times (step 9).
- Patterns 2 to 4: the same retrigger of 4 on step 5, while 1, 2 or 3 holders (Sounds 1 to 3,
  250, 350 and 500 Hz tones played for eight steps from step 1) keep voices busy.
- Patterns 5 to 8, exploratory: FX 13 (steps 1 to 8) and FX 14 (steps 5 to 12) over the
  retrigger of 4 and over a two-step 700 Hz note.
- Patterns 9 to 14: 5 s tones on Sounds 5 (700 Hz) and 6 (1000 Hz) with nibbles 3, 5, 6, 7,
  9, A, B, C, D, E and F.

This script decodes the TypeScript restore with the Python decoder into the expected
artifact, requires its packets to equal the compiler's packets.json, pins the frozen
measurement method (scripts/aux_nibble2_method.py) by hash, and writes the experiment record
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
from scripts.aux_nibble2_method import SETTINGS

DIRECTORY = "aux-nibble-002"
REGISTRATION = "aux-nibble-registration-002.json"
METHOD = "scripts/aux_nibble2_method.py"
BUILDER = "web/scripts/build-aux-nibble-2-test.ts"
STEP = SETTINGS["step_seconds"]
PASS_SECONDS = SETTINGS["chain_patterns"] * SETTINGS["steps_per_pattern"] * STEP
# Two full passes of the 56 s chain, and a margin.
PLAYBACK_SECONDS = 118
MEL_SECONDS = 5.0
HOLDER_SECONDS = 8 * STEP

PREDICTIONS = {
    "H1_one_voice": {
        "kind": "voice_onsets",
        "statement": "A drum note's repeats re-strike one voice: the retrigger of 4 plays all 4 onsets whether 0, 1, 2 or 3 other voices are held",
        "expected": {"0": 4, "1": 4, "2": 4, "3": 4},
    },
    "H2_voice_per_repeat": {
        "kind": "voice_onsets",
        "statement": "Each repeat needs a voice of its own and, like any new note, is dropped when none is free (a sounding note is never cut): with 0, 1, 2, 3 voices held the retrigger of 4 plays 4, 3, 2, 1 onsets",
        "expected": {"0": 4, "1": 3, "2": 2, "3": 1},
    },
    "H1_restart": {
        "kind": "choke",
        "model": "restart",
        "statement": "A repeat cuts the previous one and restarts the sample: the body power 12 to 52 ms after the fourth onset of the unaccompanied retrigger equals the single hit's after its onset (0 dB, within 1.5 dB)",
        "tolerance_db": 1.5,
    },
    "H2_overlap": {
        "kind": "choke",
        "model": "overlap",
        "statement": "Repeats overlap and their bodies add in power: after the fourth onset the body power is the single hit's summed at offsets 0, 62.5, 125 and 187.5 ms (predicted from the reference hit, about +4 dB), within 1.5 dB; undecided if that prediction is under 3 dB",
        "tolerance_db": 1.5,
        "min_separation_db": 3.0,
    },
    "H_holders_continue": {
        "kind": "holder_duration",
        "statement": "No holder is cut by the drum: every holder sounds its full eight steps (2.0 s, within 60 ms), as a sounding note is never cut (voice-steal-results.md)",
        "expected_seconds": HOLDER_SECONDS,
        "tolerance_seconds": 0.06,
    },
    "H_length_steps": {
        "kind": "melodic_duration",
        "statement": "A melodic note with high nibble n in 3, 5, 6, 7, 9, A, B, C, D, E sounds for n steps (250 ms each, within 60 ms)",
        "expected_seconds": {format(n, "X"): n * STEP for n in (3, 5, 6, 7, 9, 0xA, 0xB, 0xC, 0xD, 0xE)},
        "tolerance_seconds": 0.06,
    },
    "H_F_15_steps": {
        "kind": "melodic_duration",
        "statement": "Nibble F is fifteen steps like the others: 3.75 s (within 60 ms) of the 5 s tone",
        "expected_seconds": {"F": 15 * STEP},
        "tolerance_seconds": 0.06,
    },
    "H_F_whole_sample": {
        "kind": "melodic_duration",
        "statement": "Nibble F plays the whole sample: the 5 s tone sounds 5.0 s (within 100 ms)",
        "expected_seconds": {"F": MEL_SECONDS},
        "tolerance_seconds": 0.1,
    },
}

QUESTIONS = [
    "Pattern 1, second half, and Patterns 2 to 4 (the drum with low tones): did the drum burst sound the same in every bar, or thinner as more tones played? (notes)",
    "Patterns 9 to 14 (two steady tones per bar, then one): did the tones stop at different times? (notes)",
    "Patterns 5 to 8 (effects): anything notable about how the bursts and the short tone behaved? (notes)",
    "Did the device show ERR, or anything unusual on its screen? (yes/no/notes)",
    "Anything else you noticed (Enter to skip)",
]
INSTRUCTIONS = """# Aux-nibble test 2

After the restore, press PLAY and let the chain run: fourteen one-bar patterns at 60 BPM
(four seconds each, 56 s a pass). Keep the volume where you set it, and do not touch any knob
or button while it plays; the recording should hold two full passes.

- Pattern 1: a single drum hit, then a burst of four.
- Patterns 2 to 4: one, two, then three low tones, with the burst of four a second in.
- Patterns 5 to 8: the burst and a short tone under punch-in effects.
- Patterns 9 to 14: steady tones that stop after different lengths.
"""


def load_packets(path):
    view = json.loads(path.read_text())
    if view.get("schema") != "sosample.packets":
        raise ValueError("Expected a sosample packets file")
    return tuple(Packet(p["tag"], base64.b64decode(p["payload"])) for p in view["packets"])


def probes_from(project):
    """The probe layout the frozen method reads, from the builder's project.json."""
    hz = {str(h["sound"]): h["hz"] for h in project["holders"]}
    hz[str(project["melodic"]["a"]["sound"])] = project["melodic"]["a"]["hz"]
    hz[str(project["melodic"]["b"]["sound"])] = project["melodic"]["b"]["hz"]
    return {
        "drum_sound": project["drum"]["sound"],
        "hz_by_sound": hz,
        "reference": project["reference"],
        "voice_probes": project["voice_probes"],
        "holder_probes": project["holder_probes"],
        "length_probes": project["length_probes"],
        "fx_patterns": project["fx_patterns"],
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    for required in ("restore.wav", "packets.json", "project.json"):
        if not (folder / required).exists():
            raise ValueError(f"Run {BUILDER} first; missing {required}")
    if registration_path.exists() or (folder / "edited.symbols.npz").exists():
        raise ValueError("Fresh registration required")
    project = json.loads((folder / "project.json").read_text())
    if project["step_seconds"] != STEP or project["melodic"]["seconds"] != MEL_SECONDS or project["swing"] != 0:
        raise ValueError("The built restore does not match the registered timing")
    if len(project["chain"]) != SETTINGS["chain_patterns"]:
        raise ValueError("The built chain does not match the frozen method")
    if PLAYBACK_SECONDS < 2 * PASS_SECONDS + 4:
        raise ValueError("The playback recording would not hold two passes")
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
                "builder": BUILDER,
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
                "analysis_version": "aux-nibble-2-registration-0.1",
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
                "probes": probes_from(project),
                "aux_bytes": project["aux_bytes"],
                "effects": project["effects"],
                "method_script": METHOD,
                "method_script_sha256": sha256_file(root / METHOD),
                "method_settings": SETTINGS,
                "playback_seconds": PLAYBACK_SECONDS,
                "predictions": {
                    "reception": "The backup equals the compiled target exactly (every packet and the whole body), every auxiliary byte and effect included",
                    **PREDICTIONS,
                },
                "decision": [
                    "Exact reception is decided by the native check of the backup against the target",
                    "Each audible prediction is decided by the frozen method on playback.wav: onset counts by majority, durations and powers by median, over the full passes recorded",
                    "H1_one_voice and H2_voice_per_repeat exclude each other, as do H1_restart and H2_overlap, and H_F_15_steps and H_F_whole_sample; if neither of a pair holds, the result is recorded as neither, with the measurements, and no rule is adopted",
                    "The choke ratio is read only from passes where the unaccompanied retrigger played 4 onsets",
                    "The FX patterns (5 to 8), the onset offsets and the user's answers are exploratory",
                ],
                "limits": [
                    "One session on one device, at 60 BPM with no swing (aux-nibble-003 covers tempo and swing)",
                    "Onset counting assumes repeats at least 10 ms apart; the closest here are 62.5 ms",
                    "The choke reading assumes the body's noise adds in power when copies overlap; a restart that did not reset the sample's start would read as neither",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "packets": len(packets)}))


if __name__ == "__main__":
    main()
