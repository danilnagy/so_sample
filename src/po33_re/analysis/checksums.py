"""Bounded checksummed-frame hypotheses; a single hit is not validation."""

import binascii
import zlib


def scan_frame_offsets(data, payload_bytes, crc_bits):
    if crc_bits not in (16, 32) or type(payload_bytes) is not int or payload_bytes <= 0:
        raise ValueError("Positive payload length and 16/32-bit CRC required")
    frame_bytes = payload_bytes + crc_bits // 8
    if len(data) < 2 * frame_bytes:
        raise ValueError("Two real consecutive frame lengths required")
    hits = []
    comparisons = 0
    for offset in range(frame_bytes):
        payload = data[offset : offset + payload_bytes]
        tail = data[offset + payload_bytes : offset + frame_bytes]
        for initial in (0, 65535) if crc_bits == 16 else (0,):
            crc = binascii.crc_hqx(payload, initial) if crc_bits == 16 else zlib.crc32(payload)
            for final_xor in (0, 65535) if crc_bits == 16 else (0,):
                for endian in ("little", "big"):
                    comparisons += 1
                    if crc ^ final_xor == int.from_bytes(tail, endian):
                        hits.append(
                            {
                                "byte_offset": offset,
                                "initial": initial,
                                "final_xor": final_xor,
                                "endian": endian,
                            }
                        )
    return comparisons, hits


def validate_frame_candidate(data, payload_bytes, crc_bits, candidate, first_frame=10, frames=64):
    frame_bytes = payload_bytes + crc_bits // 8
    if (
        first_frame < 0
        or frames <= 0
        or len(data) < candidate["byte_offset"] + (first_frame + frames) * frame_bytes
    ):
        raise ValueError("Insufficient data for independent frame holdout")
    passed = 0
    payloads = set()
    for frame in range(first_frame, first_frame + frames):
        offset = candidate["byte_offset"] + frame * frame_bytes
        payload = data[offset : offset + payload_bytes]
        payloads.add(payload)
        tail = data[offset + payload_bytes : offset + frame_bytes]
        crc = (
            binascii.crc_hqx(payload, candidate["initial"])
            if crc_bits == 16
            else zlib.crc32(payload)
        )
        passed += (crc ^ candidate["final_xor"]) == int.from_bytes(tail, candidate["endian"])
    return {
        "holdout_first_frame": first_frame,
        "holdout_frames": frames,
        "holdout_matching_checksums": passed,
        "distinct_holdout_payloads": len(payloads),
        "all_holdout_frames_pass": passed == frames,
    }
