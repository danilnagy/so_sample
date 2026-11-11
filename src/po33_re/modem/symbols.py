"""Reversible storage of phase labels; these are not verified protocol bits."""

import io
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SCHEMA = "po33.phase-symbols"
PHASE_CONVENTION = "absolute-sign-pairs-v1:11=3,10=2,00=0,01=1"


def validate_symbols(symbols: np.ndarray) -> None:
    if not isinstance(symbols, np.ndarray) or symbols.dtype != np.uint8 or symbols.ndim != 1:
        raise ValueError("Symbols must be a one-dimensional uint8 array")
    if np.any(symbols > 3):
        raise ValueError("Phase symbols must be in range 0..3")


def pack_symbols(symbols: np.ndarray) -> tuple[bytes, dict]:
    validate_symbols(symbols)
    padding = (-len(symbols)) % 4
    values = np.pad(symbols, (0, padding)).reshape(-1, 4)
    packed = values[:, 0] | values[:, 1] << 2 | values[:, 2] << 4 | values[:, 3] << 6
    return packed.tobytes(), {
        "symbol_count": len(symbols),
        "padding_symbols": padding,
        "packing": "four-two-bit-symbols-per-byte, first-in-lowest-pair",
    }


def unpack_symbols(data: bytes, count: int) -> np.ndarray:
    if type(count) is not int or count < 0 or len(data) != (count + 3) // 4:
        raise ValueError("Packed byte length does not match symbol count")
    values = np.frombuffer(data, dtype=np.uint8)
    expanded = ((values[:, None] >> np.array([0, 2, 4, 6])) & 3).astype(np.uint8).ravel()
    if np.any(expanded[count:]):
        raise ValueError("Nonzero padding in packed symbol export")
    return expanded[:count].copy()


@dataclass
class SymbolArtifact:
    left_symbols: np.ndarray
    right_symbols: np.ndarray
    metadata: dict

    def validate(self) -> None:
        validate_symbols(self.left_symbols)
        validate_symbols(self.right_symbols)
        m = self.metadata
        if not isinstance(m, dict) or m.get("schema") != SCHEMA:
            raise ValueError("Unknown symbol artifact schema")
        if type(m.get("schema_version")) is not int or m["schema_version"] != 1:
            raise ValueError("Unsupported symbol schema version")
        if m.get("phase_convention") != PHASE_CONVENTION:
            raise ValueError("Unsupported phase convention")
        if m.get("channel_order") != ["left", "right"]:
            raise ValueError("Invalid channel order")
        if not isinstance(m.get("source_sha256"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", m["source_sha256"]
        ):
            raise ValueError("Invalid source SHA-256")
        if type(m.get("sample_rate_hz")) is not int or m["sample_rate_hz"] <= 0:
            raise ValueError("Invalid sample rate")
        if not isinstance(m.get("decoder_version"), str) or not m["decoder_version"]:
            raise ValueError("Missing decoder version")
        if not isinstance(m.get("transformations"), list):
            raise ValueError("Missing transformation provenance")  # noqa: TRY004 -- invalid schema
        if not isinstance(m.get("channels"), dict):
            raise ValueError("Missing channel metadata")  # noqa: TRY004 -- invalid schema
        for channel, symbols in (("left", self.left_symbols), ("right", self.right_symbols)):
            d = m["channels"].get(channel)
            if (
                not isinstance(d, dict)
                or type(d.get("symbol_count")) is not int
                or d["symbol_count"] != len(symbols)
            ):
                raise ValueError(f"Invalid {channel} symbol count")
            for key in ("boundaries", "discarded_samples", "uncertainty"):
                if not isinstance(d.get(key), dict):
                    raise ValueError(f"Missing {channel} {key}")  # noqa: TRY004 -- invalid schema
        # Reject non-JSON values, including NaN and infinity.
        json.dumps(m, allow_nan=False)

    def to_bytes(self) -> bytes:
        self.validate()
        output = io.BytesIO()
        np.savez(
            output,
            left_symbols=self.left_symbols,
            right_symbols=self.right_symbols,
            metadata_json=np.array(json.dumps(self.metadata, sort_keys=True, allow_nan=False)),
        )
        return output.getvalue()


def load_artifact(path: Path) -> SymbolArtifact:
    try:
        with np.load(path, allow_pickle=False) as data:
            if set(data.files) != {"left_symbols", "right_symbols", "metadata_json"}:
                raise ValueError("Unexpected symbol artifact members")
            text = data["metadata_json"]
            if text.ndim != 0 or text.dtype.kind != "U":
                raise ValueError("metadata_json must be a Unicode scalar")
            artifact = SymbolArtifact(
                data["left_symbols"].copy(), data["right_symbols"].copy(), json.loads(str(text))
            )
    except (zipfile.BadZipFile, EOFError, TypeError, AttributeError) as exc:
        raise ValueError(f"Malformed symbol artifact: {exc}") from exc
    artifact.validate()
    return artifact
