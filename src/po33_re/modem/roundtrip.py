"""Strict comparisons for software reconstruction; never a hardware restore claim."""

from pathlib import Path

import numpy as np

from ..artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from .decode import decode_wav
from .encode import DEFAULT_ENCODER_CARRIER_HZ, encode_artifact
from .symbols import SymbolArtifact


def compare_artifacts(original: SymbolArtifact, reconstructed: SymbolArtifact) -> dict:
    original.validate()
    reconstructed.validate()
    if original.metadata["phase_convention"] != reconstructed.metadata["phase_convention"]:
        raise ValueError("Cannot compare different phase conventions")
    channels = {}
    for name in ("left", "right"):
        a = getattr(original, name + "_symbols")
        b = getattr(reconstructed, name + "_symbols")
        n = min(len(a), len(b))
        changed = a[:n] != b[:n]
        edges = np.diff(np.r_[False, changed, False].astype(np.int8))
        starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
        channels[name] = {
            "original_symbols": len(a),
            "reconstructed_symbols": len(b),
            "overlap_symbols": n,
            "changed_overlap_symbols": int(np.count_nonzero(changed)),
            "tail_symbols": abs(len(a) - len(b)),
            "identical": bool(np.array_equal(a, b)),
            "changed_ranges": np.column_stack((starts, ends)).tolist(),
            "range_convention": "zero-based end-exclusive symbol indices",
            "alignment_shift": 0,
            "discarded_for_alignment": 0,
        }
    return {
        "schema_version": 1,
        "channels": channels,
        "passed": all(c["identical"] for c in channels.values()),
        "hardware_verified": False,
        "evidence": "Exact complete phase labels and counts; not verified protocol/state data",
    }


def run_roundtrip(
    capture: Path,
    directory: Path,
    threshold: float,
    rate: int = 44100,
    amplitude: float = 0.5,
    force: bool = False,
    carrier_hz: float = DEFAULT_ENCODER_CARRIER_HZ,
) -> dict:
    source = decode_wav(capture, threshold)
    waveform, encoding = encode_artifact(source, rate, amplitude, carrier_hz)
    if directory.is_symlink():
        raise ValueError("Refusing symbolic-link roundtrip directory")
    if directory.exists() and not directory.is_dir():
        raise ValueError("Roundtrip output must be a directory")
    if not directory.exists():
        directory.mkdir()
    paths = {
        name: directory / name
        for name in (
            "source.symbols.npz",
            "decode.json",
            "restore.wav",
            "encode.json",
            "restored.symbols.npz",
            "redecode.json",
            "roundtrip.json",
        )
    }
    validate_outputs(list(paths.values()), [capture], force)
    write_bytes(paths["source.symbols.npz"], source.to_bytes(), force)
    write_bytes(paths["decode.json"], json_bytes(source.metadata), force)
    write_bytes(paths["restore.wav"], waveform, force)
    encoding["output_sha256"] = sha256_file(paths["restore.wav"])
    encoding["source_artifact_sha256"] = sha256_file(paths["source.symbols.npz"])
    write_bytes(paths["encode.json"], json_bytes(encoding), force)
    restored = decode_wav(paths["restore.wav"], threshold)
    write_bytes(paths["restored.symbols.npz"], restored.to_bytes(), force)
    write_bytes(paths["redecode.json"], json_bytes(restored.metadata), force)
    report = compare_artifacts(source, restored)
    report.update(
        {
            "source_capture_sha256": source.metadata["source_sha256"],
            "restore_wav_sha256": encoding["output_sha256"],
            "decoder_threshold": threshold,
            "sample_rate_hz": rate,
            "carrier_hz": carrier_hz,
            "encoder_version": encoding["encoder_version"],
            "output_directory": str(directory),
            "boundary_policy": encoding["final_cycle_policy"],
            "acquisition_primer": encoding["acquisition_primer"],
        }
    )
    write_bytes(paths["roundtrip.json"], json_bytes(report), force)
    return report
