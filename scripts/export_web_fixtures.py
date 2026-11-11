"""Write the fixtures the TypeScript core (web/src/core) is tested against.

Every fixture is a hardware fact or a pinned reference value:

- template-empty.json: the packets of the empty device backup (experiments/empty-001-a).
- golden-<experiment>.json: a hardware-verified session whose restore was accepted
  exactly. Holds the packets, the hash of the restore WAV the device accepted, the label
  streams, the decoded fields, and where the capture WAV lives for the local decode test.
- pcm16.json: how float samples were converted to PCM16 in the accepted restores.
- mulaw.json, resample.json: codec and resampler reference vectors from the Python.

Rerun after a new verified session is added to GOLDENS. Output is deterministic.
"""

import base64
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from po33_re.audio import load_pcm_wav
from po33_re.formats.effects import step_effects
from po33_re.formats.globals import pattern_chain, swing, tempo
from po33_re.formats.packets import (
    FRAME_START_BYTE,
    decode_artifact,
    sound_data,
    sound_groups,
    wire_bytes,
)
from po33_re.formats.patterns import pattern_data
from po33_re.formats.samples import decode_signed_mulaw, encode_signed_mulaw
from po33_re.modem.symbols import load_artifact

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web/src/core/__fixtures__"
TEMPLATE = "empty-001-a"
GOLDENS = [
    "compiled-melodic-notes-writer-001",
    "compiled-fx-rules-001",
    "compiled-drum-kit-pages-001",
    "web-template-001",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def packets_json(frame):
    return [{"tag": p.tag, "payload": base64.b64encode(p.payload).decode()} for p in frame.packets]


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def decoded_view(frame):
    patterns = []
    for number in range(1, 17):
        data = pattern_data(frame, number)
        cells = {}
        for sound in range(1, 17):
            column = []
            for step in range(16):
                aux = data[768 + 16 * step + sound - 1]
                p = 48 * step + 3 * (sound - 1)
                primary = int.from_bytes(data[p : p + 3], "little")
                column.append(
                    None if aux == 0 and primary == 0 else {"aux": aux, "primary": primary}
                )
            if any(cell is not None for cell in column):
                cells[str(sound)] = column
        patterns.append(
            {"cells": cells, "effects": step_effects(frame, number), "sha256": sha(data)}
        )
    sounds = []
    for sid, indices in sorted(sound_groups(frame).items()):
        if not indices:
            sounds.append({"id": sid, "record": None})
            continue
        data = sound_data(frame, sid)
        sounds.append(
            {
                "id": sid,
                "record": {
                    "start": int.from_bytes(data[0:4], "little"),
                    "end": int.from_bytes(data[4:8], "little"),
                    "owner": data[8],
                    "codes": len(data) - 9,
                    "codes_sha256": sha(data[9:]),
                },
            }
        )
    return {
        "tempo": tempo(frame),
        "swing": swing(frame),
        "chain": pattern_chain(frame),
        "patterns": patterns,
        "sounds": sounds,
    }


def golden(name):
    folder = ROOT / "experiments" / name
    capture, restore = folder / "capture.wav", folder / "restore.wav"
    edited = load_artifact(folder / "edited.symbols.npz")
    captured = load_artifact(folder / "derived/analysis-001/capture.symbols.npz")
    observation = json.loads((folder / "hardware-observation-001.json").read_text())
    if not (observation["hardware_verified"] and observation["checks"]["session_target_exact"]):
        raise ValueError(f"{name} is not a verified exact session")
    frame = decode_artifact(edited)
    if decode_artifact(captured).encoded_body != frame.encoded_body:
        raise ValueError(f"{name}: capture differs from the restore")
    capture_samples, capture_info = load_pcm_wav(capture)
    _, restore_info = load_pcm_wav(restore)
    return {
        "experiment": name,
        "capture": {
            "path": f"experiments/{name}/capture.wav",
            "sha256": sha(capture.read_bytes()),
            "frames": capture_info["frames"],
            "sample_rate_hz": capture_info["sample_rate_hz"],
            "decoder_threshold": 0.0063,
            "peak": float(np.max(np.abs(capture_samples))),
        },
        "restore": {
            "path": f"experiments/{name}/restore.wav",
            "sha256": sha(restore.read_bytes()),
            "frames": restore_info["frames"],
            "sample_rate_hz": restore_info["sample_rate_hz"],
            "labels": {
                channel: {
                    "count": len(getattr(edited, channel + "_symbols")),
                    "sha256": sha(getattr(edited, channel + "_symbols").tobytes()),
                }
                for channel in ("left", "right")
            },
        },
        "frame": {
            "end_byte": frame.end_byte,
            "encoded_body_sha256": sha(frame.encoded_body),
            "preamble_sha256": sha(wire_bytes(edited)[:FRAME_START_BYTE]),
            "packets": packets_json(frame),
        },
        "decoded": decoded_view(frame),
    }


def template():
    folder = ROOT / "experiments" / TEMPLATE
    artifact = load_artifact(folder / "derived/analysis-001/capture.symbols.npz")
    frame = decode_artifact(artifact)
    return {
        "experiment": TEMPLATE,
        "capture_sha256": artifact.metadata["source_sha256"],
        "encoded_body_sha256": sha(frame.encoded_body),
        "packets": packets_json(frame),
        "decoded": decoded_view(frame),
    }


def pcm16():
    rng = np.random.default_rng(33)
    halves = (
        rng.integers(-32768, 32768, 500) / 32768
        + rng.choice([0, 0.5, 0.25, 0.75, 0.999], 500) / 32768
    )
    values = np.concatenate(
        [
            rng.uniform(-1, 1, 2000),
            halves,
            [1.0, -1.0, 0.5, -0.5, 0.0, 1 - 2**-24, -(1 - 2**-24)],
            # libsndfile rounds up within 2**-17 of the next integer (measured).
            [
                (k + 1 - d) / 32768
                for k in (0, 8191, -8193, 20000)
                for d in (2**-16, 2**-17, 2**-18, 1e-9)
            ],
        ]
    )
    buffer = io.BytesIO()
    sf.write(buffer, np.column_stack([values, values]), 44100, format="WAV", subtype="PCM_16")
    buffer.seek(0)
    written, _ = sf.read(buffer, dtype="int16", always_2d=True)
    return {"values": values.tolist(), "pcm16": written[:, 0].tolist()}


def mulaw():
    rng = np.random.default_rng(34)
    samples = np.concatenate([rng.uniform(-1, 1, 3000), rng.normal(0, 0.05, 3000).clip(-1, 1)])
    return {
        "levels": decode_signed_mulaw(np.arange(256, dtype=np.uint8)).tolist(),
        "encode_input": samples.tolist(),
        "encode_codes": encode_signed_mulaw(samples).tolist(),
    }


def resample():
    rng = np.random.default_rng(35)
    cases = []
    for rate, (up, down) in ((48000, (125, 256)), (44100, (625, 1176))):
        x = rng.uniform(-0.8, 0.8, rate // 10)
        y = resample_poly(x, up, down)
        cases.append(
            {
                "input_rate_hz": rate,
                "up": up,
                "down": down,
                "input": x.tolist(),
                "output": y.tolist(),
                "output_codes": encode_signed_mulaw(np.clip(y, -1, 1)).tolist(),
            }
        )
    return {"cases": cases}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write("template-empty.json", template())
    for name in GOLDENS:
        write(f"golden-{name}.json", golden(name))
    write("pcm16.json", pcm16())
    write("mulaw.json", mulaw())
    write("resample.json", resample())
    print(sorted(path.name for path in OUT.iterdir()))


if __name__ == "__main__":
    main()
