"""Register the aux-nibble-003 test: retrigger spacing and note length against tempo and swing.

The restore in experiments/aux-nibble-003 was built by web/scripts/build-aux-nibble-3-test.ts
(docs/aux-nibble-3-control.md), at 120 BPM (a 125 ms step) with swing 12 (even steps 62.5 ms
late, swing-law-results.md):

- Patterns 1 to 3: a 6 ms 5 kHz click on Sound 9 key 1, retriggered 2, 3, 4, 6 and 8 times,
  each on an odd step and an even (swung) step.
- Patterns 4 to 7: lengths 1, 2, 3 and 4 steps, each on step 1 (odd; Sound 1, a 2 s 700 Hz
  tone) and step 2 (even; Sound 2, a 2 s 1000 Hz tone).

This script decodes the TypeScript restore with the Python decoder into the expected
artifact, requires its packets to equal the compiler's packets.json, pins the frozen
measurement method (scripts/aux_nibble3_method.py) by hash, and writes the experiment record
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
from scripts.aux_nibble3_method import SETTINGS

DIRECTORY = "aux-nibble-003"
REGISTRATION = "aux-nibble-registration-003.json"
METHOD = "scripts/aux_nibble3_method.py"
BUILDER = "web/scripts/build-aux-nibble-3-test.ts"
STEP = SETTINGS["step_seconds"]
DELAY = SETTINGS["swing_delay_seconds"]
PASS_SECONDS = SETTINGS["chain_patterns"] * SETTINGS["steps_per_pattern"] * STEP
# Four full passes of the 14 s chain, and a margin.
PLAYBACK_SECONDS = 60
SPACING_N = (2, 3, 4, 6)
LENGTH_N = (1, 2, 3, 4)


def _grid_end(n, parity):
    """A note ending on the swung grid position n steps after its own (swung or not) start."""
    if n % 2 == 0:
        return n * STEP
    return n * STEP + DELAY if parity == "o" else n * STEP - DELAY


PREDICTIONS = {
    "H_spacing_scales_with_step": {
        "kind": "drum_spacing",
        "statement": "A retrigger of n divides the tempo's step evenly from wherever the note starts: repeats 125/n ms apart on odd and on even (swung) steps alike (within 3 ms)",
        "expected_seconds": {f"{n}{p}": STEP / n for n in SPACING_N for p in "oe"},
        "tolerance_seconds": 0.003,
    },
    "H_spacing_spans_swung_step": {
        "kind": "drum_spacing",
        "statement": "A retrigger of n divides the time until the next step as swing places it: an odd step lasts 1.5 steps (187.5 ms) and an even one 0.5 steps (62.5 ms), so repeats are 187.5/n ms apart on odd steps and 62.5/n ms on even ones (within 3 ms)",
        "expected_seconds": {f"{n}{p}": ((STEP + DELAY) if p == "o" else (STEP - DELAY)) / n for n in SPACING_N for p in "oe"},
        "tolerance_seconds": 0.003,
    },
    "H_spacing_fixed_time": {
        "kind": "drum_spacing",
        "statement": "Repeat spacing does not follow the tempo: 250/n ms apart, as measured at 60 BPM (within 3 ms)",
        "expected_seconds": {f"{n}{p}": 0.25 / n for n in SPACING_N for p in "oe"},
        "tolerance_seconds": 0.003,
    },
    "H_length_scales_with_step": {
        "kind": "melodic_duration",
        "statement": "A melodic length of n lasts n of the tempo's steps from the note's own start, swung or not: n x 125 ms (within 25 ms)",
        "expected_seconds": {f"{n}{p}": n * STEP for n in LENGTH_N for p in "oe"},
        "tolerance_seconds": 0.025,
    },
    "H_length_ends_on_swung_grid": {
        "kind": "melodic_duration",
        "statement": "A melodic note of length n ends where step (start + n) begins as swing places it: odd n from an odd step lasts n x 125 + 62.5 ms, from an even step n x 125 - 62.5 ms; even n lasts n x 125 ms (within 25 ms)",
        "expected_seconds": {f"{n}{p}": _grid_end(n, p) for n in LENGTH_N for p in "oe"},
        "tolerance_seconds": 0.025,
    },
    "H_length_fixed_time": {
        "kind": "melodic_duration",
        "statement": "Note length does not follow the tempo: n x 250 ms, as measured at 60 BPM (within 25 ms)",
        "expected_seconds": {f"{n}{p}": n * 0.25 for n in LENGTH_N for p in "oe"},
        "tolerance_seconds": 0.025,
    },
}

QUESTIONS = [
    "Patterns 1 to 3 (clicks): did the bursts sound evenly spaced, or did the swung ones sound squashed or stretched? (notes)",
    "Patterns 4 to 7 (two short tones a bar, a low and a high): anything notable about their lengths? (notes)",
    "Did the device show ERR, or anything unusual on its screen? (yes/no/notes)",
    "Anything else you noticed (Enter to skip)",
]
INSTRUCTIONS = """# Aux-nibble test 3

After the restore, press PLAY and let the chain run: seven one-bar patterns at 120 BPM with
swing (two seconds each, 14 s a pass). Keep the volume where you set it, and do not touch any
knob or button while it plays; the recording should hold four full passes.

- Patterns 1 to 3: bursts of 2, 3, 4, 6 and 8 clicks, each on a straight and a swung step.
- Patterns 4 to 7: two short tones a bar, 1 to 4 steps long, a low one on a straight step
  and a high one on the swung step after it.
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
            raise ValueError(f"Run {BUILDER} first; missing {required}")
    if registration_path.exists() or (folder / "edited.symbols.npz").exists():
        raise ValueError("Fresh registration required")
    project = json.loads((folder / "project.json").read_text())
    if project["step_seconds"] != STEP or project["swing_delay_seconds"] != DELAY or project["tempo"] != 120:
        raise ValueError("The built restore does not match the registered timing")
    if len(project["chain"]) != SETTINGS["chain_patterns"]:
        raise ValueError("The built chain does not match the frozen method")
    if PLAYBACK_SECONDS < 4 * PASS_SECONDS + 2:
        raise ValueError("The playback recording would not hold four passes")
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
                "analysis_version": "aux-nibble-3-registration-0.1",
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
                "method_script": METHOD,
                "method_script_sha256": sha256_file(root / METHOD),
                "method_settings": SETTINGS,
                "playback_seconds": PLAYBACK_SECONDS,
                "predictions": {
                    "reception": "The backup equals the compiled target exactly (every packet and the whole body), every auxiliary byte, the tempo and the swing included",
                    **PREDICTIONS,
                },
                "decision": [
                    "Exact reception is decided by the native check of the backup against the target",
                    "Each audible prediction is decided by the frozen method on playback.wav, by the median over the full passes recorded, each listed value within its tolerance",
                    "The three spacing hypotheses exclude each other, as do the three length hypotheses on odd lengths (on even lengths the step and swung-grid rules agree); if none holds, the result is recorded as neither, with the measurements, and no rule is adopted",
                    "Retrigger 8 (repeats 7.8 to 31.3 ms apart under the hypotheses), the onset counts, the start offsets from the grid and the user's answers are exploratory",
                ],
                "limits": [
                    "One session on one device, at one tempo and one swing value",
                    "Spacing is resolved down to about 6 ms (the onset method's minimum gap); the closest registered spacing is 10.4 ms",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "packets": len(packets)}))


if __name__ == "__main__":
    main()
