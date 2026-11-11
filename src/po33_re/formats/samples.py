"""Experimental sample interpretation supported by the local calibration tone.

The integer counter is B-controlled at start zero; end versus length semantics
at a nonzero start remain under investigation. A separate experimental preview
supports only the two observed Sound3 starts. The fractional rate is nominal.
"""

import numpy as np
from scipy.signal import resample_poly

from .packets import Packet, sound_data, sound_groups


def decode_signed_mulaw(values):
    if not isinstance(values, np.ndarray) or values.dtype != np.uint8 or values.ndim != 1:
        raise ValueError("One-dimensional uint8 sample codes required")
    coded = np.where(values & 128, values & 127, values ^ 255).astype(np.int32)
    inverted = coded ^ 255
    magnitude = ((((inverted & 15) << 3) + 132) << ((inverted >> 4) & 7)) - 132
    return np.where(inverted & 128, -magnitude, magnitude).astype(np.float64) / 32768


def encode_signed_mulaw(samples):
    """Quantize normalized mono audio to the nearest observed signed mu-law code.

    Zero uses code0; the duplicate negative-zero code255 is never emitted.
    Values above the largest decoded magnitude saturate without gain changes.
    """
    if (
        not isinstance(samples, np.ndarray)
        or samples.ndim != 1
        or samples.dtype.kind != "f"
        or not np.isfinite(samples).all()
        or np.any(abs(samples) > 1)
    ):
        raise ValueError("Finite normalized mono floating-point audio in[-1,1] required")
    codes = np.arange(255, dtype=np.uint8)
    levels = decode_signed_mulaw(codes)
    order = np.argsort(levels)
    levels, codes = levels[order], codes[order]
    upper = np.clip(np.searchsorted(levels, samples), 0, len(levels) - 1)
    lower = np.maximum(upper - 1, 0)
    nearest = np.where(abs(samples - levels[lower]) <= abs(samples - levels[upper]), lower, upper)
    return codes[nearest]


def replace_owner_codes(frame, sound_slot, codes):
    """Replace one existing melodic backing buffer without changing its size.

    All references to this owner share the replacement. Headers, packet sizes,
    ordering and every unrelated payload are preserved. No allocation is inferred.
    """
    if type(sound_slot) is not int or not 1 <= sound_slot <= 8:
        raise ValueError("A melodic backing-owner slot1..8 is required")
    if not isinstance(codes, np.ndarray) or codes.dtype != np.uint8 or codes.ndim != 1:
        raise ValueError("One-dimensional uint8 replacement codes required")
    owner_id = sound_slot - 1
    data = sound_data(frame, owner_id)
    if len(data) <= 9 or data[:4] != bytes(4) or data[8] != owner_id:
        raise ValueError("Expected an existing zero-start, self-owned sample buffer")
    if len(codes) != len(data) - 9:
        raise ValueError("Replacement must match the existing backing-buffer size exactly")
    replacement = data[:9] + codes.tobytes()
    packets, offset = list(frame.packets), 0
    for index in sound_groups(frame)[owner_id]:
        packet = packets[index]
        length = len(packet.payload)
        packets[index] = Packet(packet.tag, replacement[offset : offset + length])
        offset += length
    if offset != len(replacement):
        raise ValueError("Backing chunk sizes do not cover the replacement")
    return tuple(packets)


def extract_zero_start_sound(frame, sound_slot):
    if type(sound_slot) is not int or not 1 <= sound_slot <= 8:
        raise ValueError("Only melodic slots1..8 are supported")
    data = sound_data(frame, sound_slot - 1)
    if len(data) < 9 or data[:4] != bytes(4):
        raise ValueError("Only the observed zero-start layout is supported")
    counter = int.from_bytes(data[4:8], "little")
    owner = sound_data(frame, data[8])
    if len(owner) <= 9 or owner[8] != data[8] or owner[:4] != bytes(4):
        raise ValueError("Invalid backing data for this layout")
    raw = np.frombuffer(owner[9:], dtype=np.uint8)
    if not 0 < counter <= len(raw):
        raise ValueError("Counter exceeds available backing samples")
    return decode_signed_mulaw(raw[:counter]), {
        "sound_slot": sound_slot,
        "backing_sound_id": data[8],
        "backing_bytes": len(raw),
        "B_controlled_counter": counter,
        "sample_rate_hz_nominal": 23437.5,
        "codec": "signed-complement G711 mu-law hypothesis",
        "counter_policy": "Use counter samples at zero start; inclusive-end distinction remains unverified",
    }


def sound_at_48k(frame, sound_slot):
    samples, report = extract_zero_start_sound(frame, sound_slot)
    # 48000 / 23437.5 = 256 / 125, exactly as a nominal rate conversion.
    output = resample_poly(samples, 256, 125)
    return output, {**report, "export_sample_rate_hz": 48000, "export_frames": len(output)}


def extract_calibrated_window_sound(frame, sound_slot):
    """Experimental unpitched preview at either observed Sound3 nonzero start.

    Use[start,end) as an explicit preview convention. Exact hardware endpoint
    inclusivity remains unresolved; this does not change raw sample codes.
    """
    from .packets import calibrated_nonzero_reference

    _, start, end, owner = calibrated_nonzero_reference(frame, sound_slot)
    codes = np.frombuffer(owner[9:], dtype=np.uint8)
    return decode_signed_mulaw(codes[start:end]), {
        "sound_slot": sound_slot,
        "backing_sound_id": 0,
        "backing_bytes": len(codes),
        "start_field": start,
        "endpoint_field": end,
        "preview_code_count": end - start,
        "sample_rate_hz_nominal": 23437.5,
        "preview_selection_policy": "Explicit half-open[start,end); exact device endpoint inclusivity unresolved",
        "interpretation": "Experimental local endpoint interpretation supported by physical reference changes and user-reported minimum click",
    }


def extract_calibrated_drum_slice_sound(frame, sound_slot, slice_key):
    """Unpitched preview of Sound9 keys1/2 or either accepted Sound10/key1 copy."""
    from .drums import (
        DRUM_SLICE_CALIBRATIONS,
        calibrated_drum_copy_destination,
        calibrated_drum_slice,
    )

    if type(sound_slot) is int and sound_slot == 10:
        _, start, end, owner = calibrated_drum_copy_destination(frame, sound_slot, slice_key)
        if (start, end) not in ((0, 2000), (4045, 6045)):
            raise ValueError("Only the two accepted Sound10/key1 copied windows have previews")
        selector = 24
    else:
        _, start, end, owner = calibrated_drum_slice(frame, sound_slot, slice_key)
        selector = DRUM_SLICE_CALIBRATIONS[slice_key][0]
    codes = np.frombuffer(owner[9:], dtype=np.uint8)
    return decode_signed_mulaw(codes[start:end]), {
        "sound_slot": sound_slot,
        "slice_key": slice_key,
        "selector_id": selector,
        "backing_sound_id": 0,
        "backing_bytes": len(codes),
        "start_field": start,
        "endpoint_field": end,
        "preview_code_count": end - start,
        "sample_rate_hz_nominal": 23437.5,
        "preview_selection_policy": "Explicit half-open[start,end); exact device endpoint inclusivity unresolved",
        "pitch_and_gain_applied": False,
    }
