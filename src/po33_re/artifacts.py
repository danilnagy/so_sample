import hashlib
import json
import os
import tempfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_bytes(report: dict) -> bytes:
    return (json.dumps(report, indent=2, allow_nan=False) + "\n").encode("utf-8")


def same_path(a: Path, b: Path) -> bool:
    return a.resolve() == b.resolve() or (a.exists() and b.exists() and os.path.samefile(a, b))


def validate_outputs(outputs: list[Path], inputs: list[Path], force: bool) -> None:
    for i, output in enumerate(outputs):
        if any(same_path(output, source) for source in inputs):
            raise ValueError(f"Output aliases input: {output}")
        if any(same_path(output, other) for other in outputs[:i]):
            raise ValueError(f"Outputs alias one another: {output}")
        if output.is_symlink():
            raise ValueError(f"Refusing symbolic-link output: {output}")
        if output.exists() and (not force or not output.is_file()):
            raise ValueError(f"Output exists: {output}; use --force for regular files")
        if not output.parent.is_dir():
            raise ValueError(f"Output directory does not exist: {output.parent}")


def write_bytes(path: Path, data: bytes, force: bool = False) -> None:
    # Exclusive creation prevents a concurrent writer being overwritten without --force.
    if not force:
        with path.open("xb") as stream:
            stream.write(data)
        return
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".po33-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
