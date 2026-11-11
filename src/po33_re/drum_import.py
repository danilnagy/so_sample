"""Import 16 PCM WAV hits as one drum kit, in the layout the PO-33 writes when it records.

Observed on the device (docs/drum11-record-observation-results.md): a drum slot N (9..16)
owns sound ids 8 + 16 (N - 9) .. + 15, one per key. Recording stores one self-owned buffer
under the first id, whose 9-byte header (start, end, owner) is also key 1's window. The
other 15 ids hold 9-byte references (start, end, owner) into it. Windows are contiguous:
each starts where the previous one ends, and key k plays window k at the stored rate
(docs/drum-notes-writer-results.md).

The importer concatenates the 16 hits in key order and writes exactly that layout. Public
scope: Sound11, verified replacing its kit with the device's 102400-code capacity
(docs/drum-kit-import-results.md). By default the capacity is the kit length rounded up to
whole 4096-code pages, the unit every observed buffer uses; that default and imports into
empty slots are under test (docs/drum-kit-pages-control.md).
"""

import hashlib
import io
import os

import numpy as np
import soundfile as sf

from .artifacts import json_bytes, sha256_file, write_bytes
from .formats.packets import (
    Packet,
    decode_artifact,
    frame_report,
    rebuild_labels,
    sound_data,
    sound_groups,
)
from .formats.patterns import pattern_data
from .formats.samples import decode_signed_mulaw, encode_signed_mulaw
from .modem.decode import decode_wav
from .modem.encode import encode_artifact
from .modem.roundtrip import compare_artifacts
from .modem.symbols import load_artifact
from .sample_import import DEVICE_SAMPLE_LIMIT, prepare_pcm_sample

PAGE = 4096
# Largest drum buffer observed (device recording into Sound11).
MAX_DRUM_CAPACITY = 102400
OBSERVED_TOTAL_CAPACITY = DEVICE_SAMPLE_LIMIT  # 241 pages, hardware verified
SLICE_FRAMES = (470, 102400)
PUBLIC_DRUM_SLOTS = (11,)
SELECTOR, DATA = 0x68B5, 0xEF78


def drum_ids(drum_slot):
    if type(drum_slot) is not int or not 9 <= drum_slot <= 16:
        raise ValueError("Drum slot 9..16 required")
    first = 8 + 16 * (drum_slot - 9)
    return list(range(first, first + 16))


def _header(start, end, owner):
    return start.to_bytes(4, "little") + end.to_bytes(4, "little") + bytes([owner])


def drum_windows(frame, drum_slot):
    """Return the 16 (start, end, owner) windows of a drum slot, key 1 first, or None."""
    windows, groups = [], sound_groups(frame)
    for sid in drum_ids(drum_slot):
        data = sound_data(frame, sid) if groups.get(sid) else b""
        if len(data) < 9:
            windows.append(None)
            continue
        windows.append(
            (
                int.from_bytes(data[0:4], "little"),
                int.from_bytes(data[4:8], "little"),
                data[8],
            )
        )
    return windows


def import_drum_kit_packets(
    frame,
    drum_slot,
    hits,
    capacity=None,
    allowed_slots=PUBLIC_DRUM_SLOTS,
    total_limit=OBSERVED_TOTAL_CAPACITY,
):
    """Return packets with ``hits`` (16 native arrays, key 1 first) as the slot's kit."""
    ids = drum_ids(drum_slot)
    if drum_slot not in allowed_slots:
        raise ValueError(f"Drum slot must be one of {tuple(allowed_slots)}")
    if not isinstance(hits, list) or len(hits) != 16:
        raise ValueError("A drum kit needs 16 hits, key 1 first")
    for hit in hits:
        if (
            not isinstance(hit, np.ndarray)
            or hit.ndim != 1
            or not SLICE_FRAMES[0] <= len(hit) <= SLICE_FRAMES[1]
            or not np.isfinite(hit).all()
            or np.any(abs(hit) > 1)
        ):
            raise ValueError(f"Each hit must be {SLICE_FRAMES[0]}..{SLICE_FRAMES[1]} finite frames")
    total = sum(len(hit) for hit in hits)
    if capacity is None:
        capacity = -(-total // PAGE) * PAGE
    if type(capacity) is not int or capacity % PAGE or not total <= capacity <= MAX_DRUM_CAPACITY:
        raise ValueError(
            f"Kit of {total} codes needs a capacity in whole {PAGE}-code pages "
            f"up to {MAX_DRUM_CAPACITY}"
        )
    owner = ids[0]
    groups = sound_groups(frame)
    if any(sid not in groups for sid in ids):
        raise ValueError(f"Expected selectors for every Sound{drum_slot} id")
    existing = {sid: sound_data(frame, sid) for sid in ids if groups[sid]}
    layout = "empty"
    if existing:
        record = existing.get(owner, b"")
        owners = {data[8] for data in existing.values() if len(data) >= 9}
        borrowed = (
            len(existing) == 16
            and all(len(data) == 9 for data in existing.values())
            and len(owners) == 1
            and owners.pop() not in ids
        )
        if borrowed:
            # Every key references another sound's buffer (as Sound9/10 reference Sound1).
            # The kit gets its own buffer; the borrowed buffer stays with its owner.
            layout = f"references_to_sound_id_{existing[owner][8]}"
            lender = existing[owner][8]
            lent = sound_data(frame, lender) if groups.get(lender) else b""
            if len(lent) <= 9 or lent[8] != lender:
                raise ValueError(f"Sound{drum_slot} references a buffer that is not self-owned")
        elif (
            len(existing) != 16
            or len(record) <= 9
            or record[:4] != bytes(4)
            or record[8] != owner
            or (len(record) - 9) % PAGE
            or any(len(existing[sid]) != 9 or existing[sid][8] != owner for sid in ids[1:])
        ):
            raise ValueError(
                f"Sound{drum_slot} must be empty, one self-owned kit, or 16 references "
                "into one other buffer"
            )
        else:
            layout = "self_owned"
    other_capacity = 0
    for key, indices in groups.items():
        if not indices or key in ids:
            continue
        data = sound_data(frame, key)
        if len(data) < 9 or data[8] == owner:
            raise ValueError(f"Sound{drum_slot}'s buffer must have no outside referrers")
        if len(data) > 9:
            if data[8] != key or (len(data) - 9) % PAGE:
                raise ValueError("Unobserved backing-owner layout prevents capacity checks")
            other_capacity += len(data) - 9
    if other_capacity + capacity > total_limit:
        raise ValueError(f"Total sample capacity would exceed the limit of {total_limit} codes")
    codes = np.zeros(capacity, dtype=np.uint8)
    windows, start = [], 0
    for hit in hits:
        codes[start : start + len(hit)] = encode_signed_mulaw(hit)
        windows.append((start, start + len(hit)))
        start += len(hit)
    records = {owner: _header(*windows[0], owner) + codes.tobytes()}
    for sid, window in zip(ids[1:], windows[1:], strict=True):
        records[sid] = _header(*window, owner)
    chunks = {}
    for sid, data in records.items():
        pieces, offset = [], 0
        while offset < len(data):
            length = 4105 if offset == 0 and len(data) > 9 else PAGE
            content = data[offset : offset + length]
            pieces.extend(Packet(DATA, content[i : i + 255]) for i in range(0, len(content), 255))
            offset += length
        chunks[sid] = pieces
    packets, current = [], None
    for packet in frame.packets:
        if packet.tag == SELECTOR:
            current = packet.payload[0]
        elif packet.tag != DATA:
            current = None
        if packet.tag == DATA and current in records:
            continue
        packets.append(packet)
        if packet.tag == SELECTOR and current in records:
            packets.extend(chunks[current])
    return tuple(packets), {
        "drum_slot": drum_slot,
        "owner_sound_id": owner,
        "source_kit_was_empty": not existing,
        "source_layout": layout,
        "source_capacity_codes": max(0, len(existing.get(owner, b"")) - 9),
        "capacity_codes": capacity,
        "kit_codes": total,
        "windows": windows,
        "total_backing_capacity_codes": other_capacity + capacity,
    }


def compile_drum_kit_import(
    source_path,
    hit_paths,
    output_directory,
    drum_slot=11,
    channel=None,
    capacity=None,
    allowed_slots=PUBLIC_DRUM_SLOTS,
    total_limit=OBSERVED_TOTAL_CAPACITY,
):
    """Write a verified restore WAV with 16 WAV hits imported as a drum kit."""
    if (
        output_directory.exists()
        or output_directory.is_symlink()
        or not output_directory.parent.is_dir()
    ):
        raise ValueError("Drum-import output must be a fresh directory with existing parent")
    if len(hit_paths) != 16:
        raise ValueError("A drum kit needs 16 WAV files, key 1 first")
    source_hash = sha256_file(source_path)
    inputs = [path.read_bytes() for path in hit_paths]
    input_hashes = [hashlib.sha256(data).hexdigest() for data in inputs]
    prepared = [prepare_pcm_sample(data, channel, SLICE_FRAMES) for data in inputs]
    hits = [native for native, _ in prepared]
    source = load_artifact(source_path)
    before_bytes = source.to_bytes()
    original = decode_artifact(source)
    packets, allocation = import_drum_kit_packets(
        original, drum_slot, hits, capacity, allowed_slots, total_limit
    )
    edited = rebuild_labels(source, packets)
    edited.metadata["transformations"].append(
        {
            "kind": "bounded-drum-kit-import",
            "source_artifact_sha256": source_hash,
            "input_wav_sha256": input_hashes,
            **allocation,
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    if (
        sha256_file(source_path) != source_hash
        or [sha256_file(path) for path in hit_paths] != input_hashes
    ):
        raise ValueError("Source artifact or a hit changed during import")
    output_directory.mkdir()
    for key, data in enumerate(inputs, 1):
        write_bytes(output_directory / f"input-key{key:02d}.wav", data)
    write_bytes(output_directory / "source.symbols.npz", source_path.read_bytes())
    write_bytes(output_directory / "edited.symbols.npz", edited.to_bytes())
    restore = output_directory / "restore.unverified.wav"
    write_bytes(restore, waveform)
    recovered = decode_wav(restore, 0.02)
    write_bytes(output_directory / "redecoded.symbols.npz", recovered.to_bytes())
    decoded = decode_artifact(recovered)
    comparison = compare_artifacts(edited, recovered)
    ids = set(drum_ids(drum_slot))

    def other_packets(frame):
        current, result = None, []
        for packet in frame.packets:
            if packet.tag == SELECTOR:
                current = packet.payload[0]
            if packet.tag != DATA or current not in ids:
                result.append(packet)
        return tuple(result)

    owner = allocation["owner_sound_id"]
    codes = np.frombuffer(sound_data(target, owner)[9:], dtype=np.uint8)
    windows = drum_windows(target, drum_slot)
    expected = np.concatenate([encode_signed_mulaw(hit) for hit in hits])
    checks = {
        "source_file_unchanged": sha256_file(source_path) == source_hash,
        "inputs_unchanged": [sha256_file(path) for path in hit_paths] == input_hashes,
        "source_artifact_preserved": source.to_bytes() == before_bytes,
        "all_patterns_unchanged": all(
            pattern_data(original, n) == pattern_data(target, n) for n in range(1, 17)
        ),
        "all_other_plain_packets_unchanged": other_packets(original) == other_packets(target),
        "kit_codes_exact": np.array_equal(codes[: len(expected)], expected)
        and not np.any(codes[len(expected) :]),
        "windows_contiguous_in_key_order": [w[:2] for w in windows] == allocation["windows"]
        and all(w[2] == owner for w in windows),
        "strict_phase_roundtrip": comparison["passed"],
        "entire_target_body_after_wav_decode": decoded.encoded_body == target.encoded_body,
        "entire_target_plain_packets_after_wav_decode": decoded.packets == target.packets,
    }
    final = output_directory / ("restore.wav" if all(checks.values()) else "restore.FAILED.wav")
    os.replace(restore, final)
    kit = decode_signed_mulaw(codes[: len(expected)])
    buffer = io.BytesIO()
    sf.write(buffer, np.asarray(kit, dtype=float), 23437, format="WAV", subtype="FLOAT")
    write_bytes(output_directory / "kit-preview-23437hz.wav", buffer.getvalue())
    report = {
        "analysis_version": "bounded-drum-kit-import-0.1",
        "drum_slot": drum_slot,
        "source_artifact_sha256": source_hash,
        "source_capture_sha256": source.metadata["source_sha256"],
        "source_body_sha256": hashlib.sha256(original.encoded_body).hexdigest(),
        "input_wav_sha256": input_hashes,
        "input_audio": [info for _, info in prepared],
        "allocation": allocation,
        "target_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "restore_wav": final.name,
        "restore_wav_sha256": sha256_file(final),
        "edited_artifact_sha256": sha256_file(output_directory / "edited.symbols.npz"),
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "target_frame": frame_report(target),
        "hardware_verified": False,
        "limits": [
            f"Only slots {tuple(allowed_slots)}, empty or holding one self-owned kit, with capacity in whole pages up to {MAX_DRUM_CAPACITY}",
            f"Total sample capacity stays within {total_limit} codes (largest carried: {OBSERVED_TOTAL_CAPACITY})",
            "Hits are concatenated in key order without trimming or normalization",
            "Generated software checks are not a new hardware acceptance",
        ],
    }
    write_bytes(output_directory / "import-report.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Drum import failed software checks; report retained")
    return report
