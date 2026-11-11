import wave
from pathlib import Path

import numpy as np
import soundfile as sf

from .artifacts import sha256_file

PCM_SUBTYPES = {"PCM_U8": 8, "PCM_16": 16, "PCM_24": 24, "PCM_32": 32}


def load_pcm_wav(path: Path) -> tuple[np.ndarray, dict]:
    try:
        with sf.SoundFile(path) as audio:
            if audio.format not in {"WAV", "WAVEX"} or audio.subtype not in PCM_SUBTYPES:
                raise ValueError("Expected uncompressed integer PCM WAV")
            if audio.channels != 2:
                raise ValueError(f"Expected 2 stereo channels, found {audio.channels}")
            frames, rate, subtype = audio.frames, audio.samplerate, audio.subtype
            try:
                with wave.open(str(path), "rb") as header:
                    if header.getnframes() != frames:
                        raise ValueError(
                            "Truncated WAV: declared frame count exceeds available data"
                        )
            except wave.Error as exc:
                raise ValueError(f"Invalid PCM WAV header: {exc}") from exc
            samples = audio.read(dtype="float64", always_2d=True)
    except sf.LibsndfileError as exc:
        raise ValueError(f"Invalid WAV: {exc}") from exc
    if frames == 0 or len(samples) != frames:
        raise ValueError("Empty or truncated WAV")
    if not np.isfinite(samples).all():
        raise ValueError("Non-finite audio samples")
    return samples, {"sample_rate_hz": rate, "pcm_subtype": subtype, "frames": frames}


def inspect_wav(path: Path) -> dict:
    source_hash = sha256_file(path)
    samples, info = load_pcm_wav(path)
    frames, rate, subtype = info["frames"], info["sample_rate_hz"], info["pcm_subtype"]
    channels = {}
    threshold = 1 - 2 ** (1 - PCM_SUBTYPES[subtype])
    for index, name in enumerate(("left", "right")):
        values = samples[:, index]
        clip_count = int(np.count_nonzero(np.abs(values) >= threshold))
        channels[name] = {
            "peak_amplitude": float(np.max(np.abs(values))),
            "rms": float(np.sqrt(np.mean(values**2))),
            "possible_clipping": clip_count > 0,
            "near_full_scale_samples": clip_count,
        }
    varying = bool(np.all(np.std(samples, axis=0) > 0))
    return {
        "schema_version": 1,
        "source": str(path),
        "source_sha256": source_hash,
        "sample_rate_hz": rate,
        "pcm_subtype": subtype,
        "frames": frames,
        "duration_seconds": frames / rate,
        "channel_count": 2,
        "channels": channels,
        "channel_similarity": {
            "identical": bool(np.array_equal(samples[:, 0], samples[:, 1])),
            "correlation": float(np.corrcoef(samples.T)[0, 1]) if varying else None,
            "difference_rms": float(np.sqrt(np.mean((samples[:, 0] - samples[:, 1]) ** 2))),
        },
        "clipping_note": "Near-full-scale samples indicate possible clipping, not proof.",
    }
