"""Capture-supported staggered quadrature synthesis; hardware acceptance remains manual."""

import io
from pathlib import Path

import numpy as np
import soundfile as sf

from ..artifacts import sha256_file
from .symbols import SymbolArtifact, load_artifact

ENCODER_VERSION = "staggered-quadrature-0.2"
DEFAULT_ENCODER_CARRIER_HZ = 7812.5
# Absolute phase labels: 0=-sin, 1=-cos, 2=cos, 3=sin.
PHASE_OFFSETS = np.array([np.pi, -np.pi / 2, np.pi / 2, 0.0])


def legacy_blend_block(symbols: np.ndarray, cycles: np.ndarray, amplitude: float) -> np.ndarray:
    """Rejected 0.1 model, retained only for measured waveform comparisons."""
    indices = np.clip(np.floor(cycles).astype(np.int64), 0, len(symbols) - 1)
    following = np.minimum(indices + 1, len(symbols) - 1)
    fraction = cycles - np.floor(cycles)
    blend = np.clip((fraction - 0.6) / 0.3, 0.0, 1.0)
    angle = 2 * np.pi * cycles
    values = amplitude * (
        (1 - blend) * np.sin(angle + PHASE_OFFSETS[symbols[indices]])
        + blend * np.sin(angle + PHASE_OFFSETS[symbols[following]])
    )
    # A half-cycle acquisition primer: one low quarter then one high quarter.
    # The decoder consumes the high quarter plus the first stored high quarter.
    values[cycles < -0.25] = -amplitude
    values[(cycles >= -0.25) & (cycles < 0)] = amplitude
    return values


def synthesis_block(symbols: np.ndarray, cycles: np.ndarray, amplitude: float) -> np.ndarray:
    """Two quadrature components switch signs at their zero crossings.

    High/low phase-label coordinates denote the signs at quarter midpoints.
    I updates at 3/8 cycle to the following label's high coordinate; Q updates
    at 1/8 cycle to the current label's low coordinate. These are phase-label
    coordinates, not verified protocol bits.
    """
    i_index = np.clip(np.floor(cycles + 0.625).astype(np.int64), 0, len(symbols) - 1)
    q_index = np.clip(np.floor(cycles - 0.125).astype(np.int64), 0, len(symbols) - 1)
    i_sign = (symbols[i_index] >> 1).astype(np.float64) * 2 - 1
    q_sign = (symbols[q_index] & 1).astype(np.float64) * 2 - 1
    values = (
        amplitude
        / np.sqrt(2)
        * (
            i_sign * np.cos(2 * np.pi * (cycles - 0.125))
            + q_sign * np.cos(2 * np.pi * (cycles - 0.375))
        )
    )
    values[cycles < -0.25] = -amplitude
    values[(cycles >= -0.25) & (cycles < 0)] = amplitude
    return values


def encode_artifact(
    artifact: SymbolArtifact,
    rate: int = 44100,
    amplitude: float = 0.5,
    carrier_hz: float = DEFAULT_ENCODER_CARRIER_HZ,
) -> tuple[bytes, dict]:
    artifact.validate()
    if artifact.metadata.get("transport_extent") == "partial_clock_window":
        raise ValueError(
            "Measured-clock artifact has unobserved capture edges; rebuild the verified packet frame before waveform encoding"
        )
    if rate not in (44100, 48000):
        raise ValueError("Encoder sample rate must be 44100 or 48000 Hz")
    if not np.isfinite(amplitude) or not 0 < amplitude <= 0.9:
        raise ValueError("Encoder amplitude must be finite and in (0, 0.9]")
    if not np.isfinite(carrier_hz) or not 7600 <= carrier_hz <= 8000:
        raise ValueError("Encoder carrier must be finite and between 7600 and 8000 Hz")
    count = len(artifact.left_symbols)
    if not count or count != len(artifact.right_symbols):
        raise ValueError("Encoder requires nonempty, equal-length channel streams; no padding")
    for channel, symbols in (("left", artifact.left_symbols), ("right", artifact.right_symbols)):
        if symbols[0] not in (2, 3):
            raise ValueError(
                f"{channel}: initial phase must start high (label 2 or 3) for acquisition"
            )
        remainder = (
            artifact.metadata["channels"][channel]
            .get("boundary_sign_intervals", {})
            .get("incomplete_final_cycle_bits", [])
        )
        if remainder:
            raise ValueError(
                f"{channel}: incomplete final sign intervals cannot yet be synthesized"
            )
    # Half-cycle primer + all N full cycles + half-cycle final-phase hold guard.
    active_frames = int(np.ceil((count + 1) * rate / carrier_hz))
    silence_frames = round(0.1 * rate)
    output = io.BytesIO()
    with sf.SoundFile(
        output, mode="w", samplerate=rate, channels=2, subtype="PCM_16", format="WAV"
    ) as audio:
        audio.write(np.zeros((silence_frames, 2)))
        for start in range(0, active_frames, 65536):
            positions = np.arange(start, min(start + 65536, active_frames), dtype=np.float64)
            cycles = positions * carrier_hz / rate - 0.5
            audio.write(
                np.column_stack(
                    [
                        synthesis_block(artifact.left_symbols, cycles, amplitude),
                        synthesis_block(artifact.right_symbols, cycles, amplitude),
                    ]
                )
            )
        audio.write(np.zeros((silence_frames, 2)))
    report = {
        "schema_version": 1,
        "encoder_version": ENCODER_VERSION,
        "source_capture_sha256": artifact.metadata["source_sha256"],
        "phase_convention": artifact.metadata["phase_convention"],
        "sample_rate_hz": rate,
        "carrier_hz": carrier_hz,
        "waveform_model": "staggered quadrature sign components",
        "pcm_subtype": "PCM_16",
        "channels": 2,
        "amplitude": amplitude,
        "symbols_per_channel": count,
        "active_frames": active_frames,
        "silence_frames_each_end": silence_frames,
        "frames": active_frames + 2 * silence_frames,
        "duration_seconds": (active_frames + 2 * silence_frames) / rate,
        "preamble_policy": "Preserve all stored labels; no additional long carrier preamble.",
        "acquisition_primer": {
            "cycles": 0.5,
            "quarter_signs": [0, 1],
            "purpose": "Explicit sign-run acquisition; not captured protocol data",
        },
        "final_cycle_policy": "Synthesize final full cycle; hold final phase for half-cycle guard",
        "transition_policy": "I updates at 0.375 to next high coordinate; Q at 0.125 to current low coordinate",
        "model_evidence": "Captured quarter midpoints and waveform correlation; not hardware acceptance",
        "discarded_symbols": 0,
        "hardware_verified": False,
        "warnings": [
            "Experimental reconstruction; device acceptance is not established.",
            "Source pre-acquisition waveform and noise are not reconstructed.",
            "Primer and final hold guard are explicit synthesis conventions.",
        ],
    }
    return output.getvalue(), report


def encode_file(
    path: Path,
    rate: int = 44100,
    amplitude: float = 0.5,
    carrier_hz: float = DEFAULT_ENCODER_CARRIER_HZ,
) -> tuple[bytes, dict]:
    data, report = encode_artifact(load_artifact(path), rate, amplitude, carrier_hz)
    report["source_artifact_sha256"] = sha256_file(path)
    return data, report
