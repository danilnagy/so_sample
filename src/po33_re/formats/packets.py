"""Locally validated PO-33 framing and CRC-additive byte whitening.

The related-device lead is MIT libpo32 (Eric Lewis), pinned in the audit.
CRC mathematics uses the independent standard-library implementation. PO-33
stereo mapping and packet markers were validated against local captures.
"""

import binascii
import hashlib
from collections import Counter
from dataclasses import dataclass

import numpy as np

from ..analysis.staggered import (
    LABEL_FROM_INDEX,
    phase_increments,
    restore_labels,
    staggered_phases,
)
from ..modem.symbols import PHASE_CONVENTION, SCHEMA, SymbolArtifact

INITIAL_STATE = 0x1D0F
FRAME_START_BYTE = 4095
START_TAG = 0x985B
END_TAG = 0x826F
BYTE_VALUES = tuple(bytes([v]) for v in range(256))


@dataclass(frozen=True)
class Packet:
    tag: int
    payload: bytes


@dataclass(frozen=True)
class Frame:
    packets: tuple[Packet, ...]
    packet_spans: tuple[tuple[int, int], ...]
    end_byte: int
    encoded_body: bytes
    final_state: int


def wire_bytes(artifact):
    artifact.validate()
    increments = [
        phase_increments(staggered_phases(getattr(artifact, ch + "_symbols")))
        for ch in ("left", "right")
    ]
    # Two cells per byte, with right two-bit value before left. Keep all full
    # wire bytes; this is a diagnostic domain, not a rewrite of phase artifacts.
    count = (min(map(len, increments)) - 1) // 2 * 2
    if count <= 0:
        raise ValueError("Insufficient phase increments for a full wire byte")
    lut = np.array([0, 3, 2, 1], dtype=np.uint8)
    left, right = [lut[v[1 : count + 1]] for v in increments]
    values = np.column_stack((right, left)).ravel().reshape(-1, 4).astype(np.uint16)
    return (
        np.sum(values * np.array([1, 4, 16, 64], dtype=np.uint16), axis=1)
        .astype(np.uint8)
        .tobytes()
    )


def decode_frame(data, start=FRAME_START_BYTE):
    if not isinstance(data, bytes) or type(start) is not int or not 0 <= start < len(data):
        raise ValueError("Wire bytes and an in-range frame start required")
    pos, state = start, INITIAL_STATE

    def take(count):
        nonlocal pos, state
        if pos + count > len(data):
            raise ValueError(f"Truncated packet at wire byte{pos}")
        out = bytearray()
        for coded in data[pos : pos + count]:
            raw = (coded - (state & 255)) & 255
            state = binascii.crc_hqx(BYTE_VALUES[raw], state)
            out.append(raw)
        pos += count
        return bytes(out)

    packets, spans = [], []
    while pos < len(data):
        begin = pos
        header = take(3)
        tag = int.from_bytes(header[:2], "little")
        payload = take(header[2])
        expected = state
        trailer = take(2)
        if int.from_bytes(trailer, "little") != expected:
            raise ValueError(f"Packet checksum differs at wire byte{begin}, tag0x{tag:04x}")
        if not packets and (tag != START_TAG or payload):
            raise ValueError("Expected the observed empty start-marker packet")
        packets.append(Packet(tag, payload))
        spans.append((begin, pos))
        if tag == END_TAG:
            if payload:
                raise ValueError("Final marker has an unexpected payload")
            return Frame(tuple(packets), tuple(spans), pos, data[start:pos], state)
    raise ValueError("No verified final marker")


def decode_artifact(artifact):
    return decode_frame(wire_bytes(artifact))


def encode_packets(packets):
    packets = tuple(packets)
    if (
        not packets
        or packets[0] != Packet(START_TAG, b"")
        or packets[-1] != Packet(END_TAG, b"")
        or any(p.tag == END_TAG for p in packets[:-1])
    ):
        raise ValueError("Start/final markers and a single final packet required")
    state, out = INITIAL_STATE, bytearray()

    def emit(raw):
        nonlocal state
        out.append((raw + (state & 255)) & 255)
        state = binascii.crc_hqx(BYTE_VALUES[raw], state)

    for packet in packets:
        if type(packet.tag) is not int or not 0 <= packet.tag <= 65535:
            raise ValueError("Packet tag must be an unsigned16-bit integer")
        if not isinstance(packet.payload, bytes) or len(packet.payload) > 255:
            raise ValueError("Packet payload must contain at most255 bytes")
        for raw in packet.tag.to_bytes(2, "little") + bytes([len(packet.payload)]) + packet.payload:
            emit(raw)
        trailer = state.to_bytes(2, "little")
        for raw in trailer:
            emit(raw)
    return bytes(out)


def sound_groups(frame):
    groups, current = {}, None
    for index, packet in enumerate(frame.packets):
        if packet.tag == 0x68B5:
            if len(packet.payload) != 1 or packet.payload[0] in groups:
                raise ValueError("Unexpected or duplicate sound selector")
            current = packet.payload[0]
            groups[current] = []
        elif packet.tag == 0xEF78:
            if current is None:
                raise ValueError("Sound data has no preceding selector")
            groups[current].append(index)
    return groups


def sound_data(frame, sound_id):
    indices = sound_groups(frame).get(sound_id)
    if not indices:
        raise ValueError("Sound has no data")
    return b"".join(frame.packets[i].payload for i in indices)


def replace_reference_counter(frame, sound_slot, counter):
    """Experimental B-controlled boundary for a zero-start melodic reference."""
    if type(sound_slot) is not int or not 1 <= sound_slot <= 8:
        raise ValueError("A melodic sound slot1..8 is required")
    if type(counter) is not int:
        raise ValueError("Integer trim boundary required")
    groups = sound_groups(frame)
    indices = groups.get(sound_slot - 1)
    if not indices or len(indices) != 1:
        raise ValueError("Expected a single reference-data packet")
    index = indices[0]
    data = frame.packets[index].payload
    if len(data) != 9 or data[:4] != bytes(4):
        raise ValueError("Only the observed nine-byte zero-start reference is supported")
    owner = sound_data(frame, data[8])
    if len(owner) <= 9 or owner[:4] != bytes(4) or owner[8] != data[8]:
        raise ValueError("Backing data does not match the observed owner layout")
    if not 79 <= counter <= len(owner) - 9 - 80:
        raise ValueError("Counter outside the observed minimum/maximum guard bounds")
    replacement = data[:4] + counter.to_bytes(4, "little") + data[8:]
    packets = list(frame.packets)
    packets[index] = Packet(frame.packets[index].tag, replacement)
    return tuple(packets)


# Each fixed start has its own local measured/tested endpoint interval.
# These are calibration guards, not a general start+minimum-width formula.
CALIBRATED_WINDOW_ENDPOINTS = {31393: (31504, 65535), 11716: (11827, 19716)}


def calibrated_nonzero_reference(frame, sound_slot):
    """Validate the two observed Sound3 starts and their local endpoint intervals.

    Minimum-width quantization, endpoint inclusivity and interpolated starts remain
    unresolved. These are local calibration guards, not general trim limits.
    """
    if type(sound_slot) is not int or sound_slot != 3:
        raise ValueError("Only the locally calibrated nonzero-start Sound3 is supported")
    indices = sound_groups(frame).get(2)
    if not indices or len(indices) != 1:
        raise ValueError("Expected one Sound3 reference packet")
    index = indices[0]
    data = frame.packets[index].payload
    if len(data) != 9 or data[8] != 0:
        raise ValueError("Expected the observed nine-byte owner0 reference")
    start, end = int.from_bytes(data[:4], "little"), int.from_bytes(data[4:8], "little")
    bounds = CALIBRATED_WINDOW_ENDPOINTS.get(start)
    if bounds is None or not bounds[0] <= end <= bounds[1]:
        raise ValueError("Only calibrated Sound3 start/endpoint intervals are supported")
    owner = sound_data(frame, 0)
    if len(owner) != 65545 or owner[:4] != bytes(4) or owner[8] != 0:
        raise ValueError("Expected the observed zero-start self-owned65536-code backing buffer")
    return index, start, end, owner


def replace_calibrated_reference_end(frame, sound_slot, endpoint):
    """Experimental endpoint edit at either locally calibrated Sound3 start."""
    _, start, _, _ = calibrated_nonzero_reference(frame, sound_slot)
    return replace_calibrated_reference_window(frame, sound_slot, start, endpoint)


def replace_calibrated_reference_window(frame, sound_slot, start, endpoint):
    """Set an explicit window at one of two observed starts, preserving all other data."""
    index, _, _, _ = calibrated_nonzero_reference(frame, sound_slot)
    if type(start) is not int or start not in CALIBRATED_WINDOW_ENDPOINTS:
        raise ValueError("An exactly observed integer start11716 or31393 is required")
    low, high = CALIBRATED_WINDOW_ENDPOINTS[start]
    if type(endpoint) is not int or not low <= endpoint <= high:
        raise ValueError("Integer endpoint in this start's local calibration interval required")
    packet = frame.packets[index]
    replacement = start.to_bytes(4, "little") + endpoint.to_bytes(4, "little") + packet.payload[8:]
    packets = list(frame.packets)
    packets[index] = Packet(packet.tag, replacement)
    return tuple(packets)


def frame_report(frame):
    groups = sound_groups(frame)
    sounds = []
    for sound_id, indices in groups.items():
        if not indices:
            continue
        data = b"".join(frame.packets[i].payload for i in indices)
        sounds.append(
            {
                "sound_id": sound_id,
                "packet_count": len(indices),
                "payload_bytes": len(data),
                "header_hex": data[:9].hex(),
                "payload_sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return {
        "codec_version": "po33-crc-additive-0.1",
        "frame_start_byte": FRAME_START_BYTE,
        "frame_end_byte": frame.end_byte,
        "required_complete_label_span": [0, 2 * frame.end_byte + 3],
        "packet_count": len(frame.packets),
        "all_packet_checksums_valid": True,
        "encoded_body_sha256": hashlib.sha256(frame.encoded_body).hexdigest(),
        "tags": {
            f"0x{tag:04x}": count for tag, count in Counter(p.tag for p in frame.packets).items()
        },
        "sounds": sounds,
    }


def rebuild_labels(source, packets, carrier_cells=128):
    """Render verified protocol bytes with an explicit new constant-carrier ending."""
    if type(carrier_cells) is not int or not 64 <= carrier_cells <= 1024:
        raise ValueError("Canonical carrier extension must be64..1024 cells")
    original = decode_artifact(source)
    encoded = encode_packets(packets)
    begin = 1 + 2 * FRAME_START_BYTE
    channel_bits = np.frombuffer(encoded, dtype=np.uint8)
    qright = np.column_stack((channel_bits & 3, (channel_bits >> 4) & 3)).ravel()
    qleft = np.column_stack(((channel_bits >> 2) & 3, (channel_bits >> 6) & 3)).ravel()
    labels, channels = {}, {}
    for ch, q in zip(("left", "right"), (qleft, qright)):
        raw = getattr(source, ch + "_symbols")
        phases = staggered_phases(raw)
        body = ((phases[begin] + np.cumsum((-q.astype(np.int16)) % 4)) % 4).astype(np.uint8)
        rebuilt = np.r_[phases[: begin + 1], body, np.full(carrier_cells, body[-1], dtype=np.uint8)]
        labels[ch] = restore_labels(
            rebuilt, int(raw[0] >> 1), int(LABEL_FROM_INDEX[rebuilt[-1]] & 1)
        )
        channels[ch] = {
            "symbol_count": len(labels[ch]),
            "boundaries": {"canonical_carrier_cells": carrier_cells},
            "discarded_samples": {},
            "uncertainty": {},
            "boundary_sign_intervals": {"incomplete_final_cycle_bits": []},
        }
    metadata = {
        "schema": SCHEMA,
        "schema_version": 1,
        "phase_convention": PHASE_CONVENTION,
        "channel_order": ["left", "right"],
        "source_sha256": source.metadata["source_sha256"],
        "sample_rate_hz": source.metadata["sample_rate_hz"],
        "decoder_version": "verified-packet-label-builder-0.1",
        "channels": channels,
        "transformations": [
            {
                "kind": "verified-packet-rebuild",
                "source_frame_end_byte": original.end_byte,
                "encoded_body_sha256": hashlib.sha256(encoded).hexdigest(),
                "carrier_cells": carrier_cells,
                "source_artifact_preserved": True,
            }
        ],
        "hardware_verified": False,
    }
    artifact = SymbolArtifact(labels["left"], labels["right"], metadata)
    artifact.validate()
    if decode_artifact(artifact).encoded_body != encoded:
        raise ValueError("Rebuilt phases do not preserve the encoded packet body")
    return artifact


def set_sample_window(frame, sound_slot, start, end):
    """Set the start and end codes of a melodic slot's self-owned sample record.

    The record's 9-byte header is (start, end, owner); the window must lie within the
    buffer. Everything else is preserved. Hardware behaviour of a nonzero start on a
    self-owned record is under test (docs/sample-window-control.md).
    """
    if type(sound_slot) is not int or not 1 <= sound_slot <= 8:
        raise ValueError("A melodic sound slot 1..8 is required")
    sid = sound_slot - 1
    indices = sound_groups(frame).get(sid)
    if not indices:
        raise ValueError(f"Sound{sound_slot} has no sample record")
    first = frame.packets[indices[0]]
    data = sound_data(frame, sid)
    capacity = len(data) - 9
    if capacity <= 0 or data[8] != sid or len(first.payload) < 9:
        raise ValueError(f"Sound{sound_slot} must own its sample buffer")
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= capacity:
        raise ValueError(f"Window must satisfy 0 <= start < end <= {capacity}")
    header = start.to_bytes(4, "little") + end.to_bytes(4, "little")
    packets = list(frame.packets)
    packets[indices[0]] = Packet(first.tag, header + first.payload[8:])
    return tuple(packets)
