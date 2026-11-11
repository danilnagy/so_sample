"""Small synthetic PO-33 frames and captures for tests that must not need recordings.

The frame mimics the observed layout (two 0x7d5c global records, one sound, sixteen
1032-byte patterns) but carries no real device data. Labels are built by inverting
the wire-byte mapping independently of the packet rebuild code.
"""

import io

import numpy as np
import soundfile as sf

from po33_re.analysis.staggered import restore_labels
from po33_re.formats.packets import (
    END_TAG,
    FRAME_START_BYTE,
    START_TAG,
    Packet,
    decode_artifact,
    encode_packets,
)
from po33_re.modem.encode import encode_artifact
from po33_re.modem.symbols import PHASE_CONVENTION, SCHEMA, SymbolArtifact

INCREMENT_FROM_WIRE = np.array([0, 3, 2, 1], dtype=np.uint8)
EMPTY_PATTERN = bytes(1024) + b"\xff" * 8


def pattern_bytes(cells=(), footer=b"\xff" * 8):
    data = bytearray(EMPTY_PATTERN)
    for step, sound, primary, auxiliary in cells:
        p, a = 48 * (step - 1) + 3 * (sound - 1), 768 + 16 * (step - 1) + sound - 1
        data[p : p + 3] = bytes.fromhex(primary)
        data[a] = auxiliary
    data[1024:] = footer
    return bytes(data)


def synthetic_packets(patterns=None, tempo=120, sound_header=bytes(9)):
    patterns = patterns or {}
    second = bytearray(range(140))
    second[129:132] = bytes([tempo, 0, 7])
    packets = [
        Packet(START_TAG, b""),
        Packet(0x7D5C, bytes(140)),
        Packet(0x7D5C, bytes(second)),
        Packet(0x68B5, b"\x02"),
        Packet(0xEF78, sound_header + bytes(range(200))),
    ]
    for number in range(16):
        packets.append(Packet(0xA041, bytes([number])))
        data = patterns.get(number + 1, EMPTY_PATTERN)
        packets.extend(Packet(0xC498, data[i : i + 255]) for i in range(0, 1032, 255))
    packets.append(Packet(END_TAG, b""))
    return tuple(packets)


def artifact_from_packets(packets, source_sha256="0" * 64):
    wire = np.frombuffer(bytes(FRAME_START_BYTE) + encode_packets(packets), dtype=np.uint8)
    right = np.column_stack((wire & 3, (wire >> 4) & 3)).ravel()
    left = np.column_stack(((wire >> 2) & 3, (wire >> 6) & 3)).ravel()
    streams = []
    for cells in (left, right):
        increments = np.r_[0, 0, INCREMENT_FROM_WIRE[cells], 0].astype(np.int64)
        phases = (np.cumsum(increments) % 4).astype(np.uint8)
        streams.append(restore_labels(phases, 1, 0))
    channels = {
        name: {
            "symbol_count": len(labels),
            "boundaries": {},
            "discarded_samples": {},
            "uncertainty": {},
            "boundary_sign_intervals": {"incomplete_final_cycle_bits": []},
        }
        for name, labels in zip(("left", "right"), streams)
    }
    artifact = SymbolArtifact(
        streams[0],
        streams[1],
        {
            "schema": SCHEMA,
            "schema_version": 1,
            "phase_convention": PHASE_CONVENTION,
            "channel_order": ["left", "right"],
            "source_sha256": source_sha256,
            "sample_rate_hz": 44100,
            "decoder_version": "synthetic-test-frame",
            "transformations": [],
            "channels": channels,
            "hardware_verified": False,
        },
    )
    artifact.validate()
    assert decode_artifact(artifact).packets == packets
    return artifact


def capture_samples(artifact, level=0.15, lead_seconds=1.0, tail_seconds=2.0, rate=44100):
    """Integer PCM as an interface would deliver a device backup of ``artifact``."""
    wav, _ = encode_artifact(artifact, rate, 0.5)
    values, _ = sf.read(io.BytesIO(wav), dtype="float64", always_2d=True)
    values = np.vstack(
        [
            np.zeros((round(lead_seconds * rate), 2)),
            values * (level / 0.5),
            np.zeros((round(tail_seconds * rate), 2)),
        ]
    )
    return np.round(values * 32767).astype(np.int16)


def blocks(samples, size=2205):
    return [samples[i : i + size] for i in range(0, len(samples), size)]


def tone(seconds, level=0.1, hz=500.0, lead_seconds=1.0, rate=44100):
    t = np.arange(round(seconds * rate)) / rate
    values = np.r_[np.zeros(round(lead_seconds * rate)), level * np.sin(2 * np.pi * hz * t)]
    return np.round(np.column_stack((values, values)) * 32767).astype(np.int16)
