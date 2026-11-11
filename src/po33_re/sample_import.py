"""Conservative PCM WAV import into empty or unshared melodic slots (public scope: Sound6, Sound7)."""

import hashlib
import io
import os
import wave

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from .artifacts import json_bytes, sha256_file, write_bytes
from .audio import PCM_SUBTYPES
from .formats.packets import (
    Packet,
    decode_artifact,
    frame_report,
    rebuild_labels,
    sound_data,
    sound_groups,
)
from .formats.patterns import pattern_data
from .formats.samples import decode_signed_mulaw, encode_signed_mulaw, sound_at_48k
from .modem.decode import decode_wav
from .modem.encode import encode_artifact
from .modem.roundtrip import compare_artifacts
from .modem.symbols import load_artifact

CAPACITIES = (4096, 32768, 36864)
MIN_FRAMES, MAX_FRAMES = 2344, 30912
CALIBRATION_BUDGET = 172032
# Hardware-verified sample memory: 241 pages of 4096 codes (docs/sample-memory-limit-results.md).
# A larger restore ends in ERR and keeps only a 241-page prefix of the stream.
DEVICE_SAMPLE_LIMIT = 241 * 4096
PAGE = 4096


def prepare_pcm_sample(wav_bytes, channel=None, frame_range=(MIN_FRAMES, MAX_FRAMES)):
    """Read integer PCM mono/stereo at44.1/48k; resample without normalization.

    ``frame_range`` bounds the native length; drum slices use a shorter minimum.
    """
    if channel not in (None, "left", "right", "mix"):
        raise ValueError("Channel must be left, right or mix")
    try:
        with sf.SoundFile(io.BytesIO(wav_bytes)) as audio:
            if audio.format not in ("WAV", "WAVEX") or audio.subtype not in PCM_SUBTYPES:
                raise ValueError("Sample input must be uncompressed integer PCM WAV")
            if audio.channels not in (1, 2) or audio.samplerate not in (44100, 48000):
                raise ValueError("Sample input must be mono/stereo PCM at44100 or48000Hz")
            frames, rate, channels, subtype = (
                audio.frames,
                audio.samplerate,
                audio.channels,
                audio.subtype,
            )
            with wave.open(io.BytesIO(wav_bytes), "rb") as header:
                if header.getnframes() != frames:
                    raise ValueError("Truncated sample WAV")
            up, down = (125, 256) if rate == 48000 else (625, 1176)
            count = (frames * up + down - 1) // down
            low, high = frame_range
            if not low <= count <= high:
                raise ValueError(
                    f"Sample must convert to {low}..{high} native frames "
                    f"(about {low / 23437.5:.3f}..{high / 23437.5:.3f} seconds)"
                )
            samples = audio.read(dtype="float64", always_2d=True)
    except (sf.LibsndfileError, wave.Error, EOFError) as exc:
        raise ValueError(f"Invalid sample WAV: {exc}") from exc
    if len(samples) != frames or not np.isfinite(samples).all() or np.any(abs(samples) > 1):
        raise ValueError("Sample must contain finite normalized PCM without truncation")
    if channels == 1:
        if channel == "right":
            raise ValueError("Mono input has no right channel")
        mono, policy = samples[:, 0], "mono"
    elif channel is None:
        if not np.array_equal(samples[:, 0], samples[:, 1]):
            raise ValueError("Stereo channels differ; select --channel left, right or mix")
        mono, policy = samples[:, 0], "identical stereo: left"
    elif channel == "mix":
        mono, policy = samples.mean(axis=1), "stereo mean"
    else:
        mono, policy = samples[:, 0 if channel == "left" else 1], f"stereo {channel}"
    native = resample_poly(mono, up, down)
    if not np.isfinite(native).all() or np.any(abs(native) > 1):
        raise ValueError("Resampling exceeded normalized range; lower the source sample level")
    return native, {
        "input_frames": frames,
        "input_sample_rate_hz": rate,
        "input_channels": channels,
        "input_pcm_subtype": subtype,
        "channel_policy": policy,
        "resampling_ratio": [up, down],
        "native_frames": len(native),
        "sample_rate_hz_nominal": 23437.5,
        "gain_normalization": False,
        "native_peak": float(np.max(abs(native))),
    }


# Sound6: several import tests; Sound7: registered import test on 2026-10-10.
PUBLIC_IMPORT_SLOTS = (6, 7)


def import_sound6_packets(frame, sound_slot, native, capacity=None):
    """Populate empty or replace unshared zero-start Sound6 using verified capacities."""
    if type(sound_slot) is not int or sound_slot != 6:
        raise ValueError("Only calibrated melodic Sound6 import is supported")
    return import_melodic_sample_packets(frame, sound_slot, native, capacity, (6,))


def import_melodic_sample_packets(
    frame,
    sound_slot,
    native,
    capacity=None,
    allowed_slots=PUBLIC_IMPORT_SLOTS,
    total_limit=CALIBRATION_BUDGET,
    max_frames=MAX_FRAMES,
    page_capacity=False,
    replace_borrowed=False,
):
    """Populate an empty, or replace an unshared zero-start, melodic slot.

    With ``replace_borrowed``, a slot whose record is a 9-byte reference into another
    sound's self-owned buffer (as Sound2, 3 and 8 reference Sound1) gets its own buffer;
    the lender's buffer and its other referrers are unchanged.

    ``max_frames`` and ``page_capacity`` widen the verified length and capacity set: with
    ``page_capacity`` any whole number of 4096-code pages that fits is allowed, and the
    default capacity is the length rounded up to whole pages.

    The slot's sound id is slot - 1, and a self-owned record stores that id as its owner
    byte, as observed for Sound4, Sound5 and Sound6. ``allowed_slots`` limits which slots
    may be written; the public default is the hardware-verified Sound6.
    """
    if type(sound_slot) is not int or sound_slot not in allowed_slots or not 1 <= sound_slot <= 8:
        raise ValueError(f"Melodic slot must be one of {tuple(allowed_slots)}")
    sid = sound_slot - 1
    if (
        not isinstance(native, np.ndarray)
        or native.ndim != 1
        or not MIN_FRAMES <= len(native) <= max_frames
    ):
        raise ValueError(f"Native sample length must be {MIN_FRAMES}..{max_frames} frames")
    quantized = encode_signed_mulaw(native)
    if capacity is None:
        capacity = (
            -(-len(native) // PAGE) * PAGE
            if page_capacity
            else next((value for value in CAPACITIES if value >= len(native)), None)
        )
    allowed = (
        type(capacity) is int and capacity % PAGE == 0 if page_capacity else capacity in CAPACITIES
    )
    if type(capacity) is not int or not allowed or capacity < len(native):
        raise ValueError(
            "Capacity must be whole 4096-code pages and fit the sample"
            if page_capacity
            else "Capacity must be4096,32768 or36864 codes and fit the sample"
        )
    groups = sound_groups(frame)
    if sid not in groups:
        raise ValueError(f"Expected an existing Sound{sound_slot} selector")
    old = b"".join(frame.packets[i].payload for i in groups[sid])
    other_capacity = 0
    for key, indices in groups.items():
        if not indices:
            continue
        data = sound_data(frame, key)
        if len(data) < 9 or (data[8] == sid and key != sid):
            raise ValueError(
                f"Sound{sound_slot} must have no other referrers or malformed sample records"
            )
        if len(data) > 9:
            # A nonzero start window on another owner is verified (sample-window test).
            if data[8] != key or (len(data) - 9) % 4096:
                raise ValueError("Unobserved backing-owner layout prevents capacity checks")
            if key != sid:
                other_capacity += len(data) - 9
    borrowed = len(old) == 9 and old[8] != sid
    if borrowed:
        if not replace_borrowed:
            raise ValueError(
                f"Sound{sound_slot} references another buffer: unsupported layout "
                "unless replace_borrowed is set"
            )
        lender = old[8]
        lent = sound_data(frame, lender) if groups.get(lender) else b""
        if len(lent) <= 9 or lent[8] != lender:
            raise ValueError(f"Sound{sound_slot} references a buffer that is not self-owned")
    elif old:
        count = len(old) - 9
        start = int.from_bytes(old[:4], "little")
        endpoint = int.from_bytes(old[4:8], "little")
        # A nonzero start window on the old record is a verified trim (sample-window test).
        if (
            (count % PAGE if page_capacity else count not in CAPACITIES)
            or old[8] != sid
            or not 0 <= start < endpoint
            or not MIN_FRAMES <= endpoint <= (count if page_capacity else min(count, MAX_FRAMES))
        ):
            raise ValueError(f"Expected a calibrated self-owned Sound{sound_slot} layout")
        indices = groups[sid]
        if indices != list(range(indices[0], indices[-1] + 1)) or [
            len(frame.packets[i].payload) for i in indices
        ] != [255] * 16 + [25] + ([255] * 16 + [16]) * (count // 4096 - 1):
            raise ValueError("Expected contiguous calibrated sample-page packet geometry")
    if other_capacity + capacity > total_limit:
        raise ValueError(f"Import exceeds the {total_limit}-code total sample budget")
    codes = np.zeros(capacity, dtype=np.uint8)
    codes[: len(quantized)] = quantized
    data = bytes(4) + len(quantized).to_bytes(4, "little") + bytes([sid]) + codes.tobytes()
    chunks = []
    offset = 0
    for page in range(capacity // 4096):
        length = 4105 if page == 0 else 4096
        content = data[offset : offset + length]
        chunks.extend(Packet(0xEF78, content[i : i + 255]) for i in range(0, len(content), 255))
        offset += length
    if offset != len(data):
        raise ValueError("Page construction does not cover the imported record")
    if old:
        first, last = groups[sid][0], groups[sid][-1]
        packets = frame.packets[:first] + tuple(chunks) + frame.packets[last + 1 :]
    else:
        index = next(i for i, p in enumerate(frame.packets) if p == Packet(0x68B5, bytes([sid])))
        packets = frame.packets[: index + 1] + tuple(chunks) + frame.packets[index + 1 :]
    return packets, {
        "sound_slot": sound_slot,
        "source_record_was_empty": not bool(old),
        "source_record_was_borrowed": borrowed,
        "source_capacity_codes": max(0, len(old) - 9),
        "source_header_hex": old[:9].hex(),
        "capacity_codes": capacity,
        "endpoint": len(quantized),
        "zero_tail_codes": capacity - len(quantized),
        "total_backing_capacity_codes": other_capacity + capacity,
    }


def compile_sample_import(
    source_path,
    sample_path,
    output_directory,
    sound_slot=6,
    channel=None,
    capacity=None,
    allowed_slots=PUBLIC_IMPORT_SLOTS,
    total_limit=CALIBRATION_BUDGET,
    max_frames=MAX_FRAMES,
    page_capacity=False,
    replace_borrowed=False,
):
    if (
        output_directory.exists()
        or output_directory.is_symlink()
        or not output_directory.parent.is_dir()
    ):
        raise ValueError("Sample-import output must be a fresh directory with existing parent")
    source_hash = sha256_file(source_path)
    input_bytes = sample_path.read_bytes()
    input_hash = hashlib.sha256(input_bytes).hexdigest()
    native, input_report = prepare_pcm_sample(input_bytes, channel, (MIN_FRAMES, max_frames))
    source = load_artifact(source_path)
    before_bytes = source.to_bytes()
    original = decode_artifact(source)
    packets, allocation = import_melodic_sample_packets(
        original,
        sound_slot,
        native,
        capacity,
        allowed_slots,
        total_limit,
        max_frames,
        page_capacity,
        replace_borrowed,
    )
    sid = sound_slot - 1
    edited = rebuild_labels(source, packets)
    edited.metadata["transformations"].append(
        {
            "kind": "bounded-PCM-sample-import",
            "source_artifact_sha256": source_hash,
            "input_wav_sha256": input_hash,
            **allocation,
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    preview, preview_report = sound_at_48k(target, sound_slot)
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    if sha256_file(source_path) != source_hash or sha256_file(sample_path) != input_hash:
        raise ValueError("Source artifact or sample changed during import")
    output_directory.mkdir()
    write_bytes(output_directory / "input-sample.wav", input_bytes)
    write_bytes(output_directory / "source.symbols.npz", source_path.read_bytes())
    write_bytes(output_directory / "edited.symbols.npz", edited.to_bytes())
    restore = output_directory / "restore.unverified.wav"
    write_bytes(restore, waveform)
    buffer = io.BytesIO()
    sf.write(buffer, preview, 48000, format="WAV", subtype="FLOAT")
    write_bytes(output_directory / "preview.wav", buffer.getvalue())
    recovered = decode_wav(restore, 0.02)
    write_bytes(output_directory / "redecoded.symbols.npz", recovered.to_bytes())
    decoded = decode_artifact(recovered)
    comparison = compare_artifacts(edited, recovered)

    def other_packets(frame):
        current, result = None, []
        for packet in frame.packets:
            if packet.tag == 0x68B5:
                current = packet.payload[0]
            if packet.tag != 0xEF78 or current != sid:
                result.append(packet)
        return tuple(result)

    data = sound_data(target, sid)
    codes = np.frombuffer(data[9:], dtype=np.uint8)
    checks = {
        "source_file_unchanged": sha256_file(source_path) == source_hash,
        "input_file_unchanged": sha256_file(sample_path) == input_hash,
        "source_artifact_preserved": source.to_bytes() == before_bytes,
        "source_and_input_copies_match": sha256_file(output_directory / "source.symbols.npz")
        == source_hash
        and sha256_file(output_directory / "input-sample.wav") == input_hash,
        "all_patterns_unchanged": all(
            pattern_data(original, n) == pattern_data(target, n) for n in range(1, 17)
        ),
        "all_other_plain_packets_unchanged": other_packets(original) == other_packets(target),
        "imported_codes_exact": np.array_equal(codes[: len(native)], encode_signed_mulaw(native))
        and not np.any(codes[len(native) :]),
        "all_native_checksums": True,
        "strict_phase_roundtrip": comparison["passed"],
        "entire_target_body_after_wav_decode": decoded.encoded_body == target.encoded_body,
        "entire_target_plain_packets_after_wav_decode": decoded.packets == target.packets,
    }
    final = output_directory / ("restore.wav" if all(checks.values()) else "restore.FAILED.wav")
    os.replace(restore, final)
    restore = final
    error = decode_signed_mulaw(codes[: len(native)]) - native
    report = {
        "analysis_version": "bounded-melodic-PCM-import-0.2",
        "sound_slot": sound_slot,
        "source_artifact_sha256": source_hash,
        "source_capture_sha256": source.metadata["source_sha256"],
        "source_body_sha256": hashlib.sha256(original.encoded_body).hexdigest(),
        "input_wav_sha256": input_hash,
        "input_audio": input_report,
        "allocation": allocation,
        "target_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "target_sound_payload_sha256": hashlib.sha256(data).hexdigest(),
        "target_sound_header_hex": data[:9].hex(),
        "restore_wav": restore.name,
        "restore_wav_sha256": sha256_file(restore),
        "edited_artifact_sha256": sha256_file(output_directory / "edited.symbols.npz"),
        "quantization_error_rms": float(np.sqrt(np.mean(error**2))),
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "target_frame": frame_report(target),
        "preview": preview_report,
        "hardware_verified": False,
        "limits": [
            "Only empty or unshared zero-start Sound6 using4096/32768/36864-code capacities and2344..30912 native frames is supported",
            "Automatic capacity uses the smallest verified size that fits; calibration budget172032 is not a hardware memory-limit claim",
            "Mono and explicitly selected/mixed stereo integer PCM at44.1/48k are supported;44.1k mono and new duration combinations need appropriate hardware evidence",
            "Existing slot parameters, samples and patterns are retained; preview does not apply device pitch/filter/gain",
            "Generated software checks are not a new hardware acceptance",
        ],
    }
    write_bytes(output_directory / "import-report.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Sample import failed software checks; report retained")
    return report
