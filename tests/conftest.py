"""Shared pytest configuration.

Many tests read the research captures and their derived symbols (experiments/**/*.wav,
*.npz, derived/), which git ignores: they are recordings of the research device, about
12 GB, and are not published. A test whose fixture opens one of those files skips with the
missing path, instead of erroring, so a fresh clone runs the rest of the suite cleanly.
Any other missing file still fails.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"


def _is_capture(path: str | None) -> bool:
    if not path:
        return False
    try:
        resolved = Path(path).resolve()
    except OSError:
        return False
    return EXPERIMENTS in resolved.parents


def _skip_if_capture(error: BaseException) -> None:
    if isinstance(error, FileNotFoundError) and _is_capture(error.filename):
        pytest.skip(f"research capture not present: {Path(error.filename).relative_to(ROOT)}")


# Setup, not fixture setup: a module-scoped fixture's error is cached and raised again for
# every later test without calling the fixture hook.
@pytest.hookimpl(wrapper=True)
def pytest_runtest_setup(item):
    try:
        return (yield)
    except FileNotFoundError as error:
        _skip_if_capture(error)
        raise


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    try:
        return (yield)
    except FileNotFoundError as error:
        _skip_if_capture(error)
        raise
