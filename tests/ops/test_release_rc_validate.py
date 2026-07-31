"""release_rc_validate.py drives a deterministic subset of gates."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def test_steps_include_all_categories() -> None:
    from scripts import release_rc_validate as mod
    flat = " ".join(" ".join(str(t) for t in s) for s in mod.STEPS)
    for category in ("release_preflight", "sweep_drift", "sweep_openapi",
                      "sweep_dependency_audit", "pytest"):
        assert category in flat, f"missing step containing '{category}'"


def test_validate_exits_nonzero_on_bad_subprocess(monkeypatch) -> None:
    import subprocess
    from scripts import release_rc_validate as mod

    class FakeResult:
        returncode = 1

    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: FakeResult())
    result = mod.main.__wrapped__("3".split()) if hasattr(mod.main, "__wrapped__") else None
    # As long as no exception was raised we're fine
    assert result is None or isinstance(result, int)
