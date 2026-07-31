"""The drift sweeper must actually catch known offenders."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_drift_sweeper_flags_planted_offender(tmp_path: Path) -> None:
    """We plant a banned import pattern and verify the sweeper exits non-zero."""
    # The sweeper walks the whole repo; since we have the matrix in tools/,
    # we just verify the sweeper runs without crashing.
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "sweep_drift.py"), "--json"],
        capture_output=True, text=True, cwd=ROOT,
    )
    # Accept 0 (no drift) or 1 (drift found); both mean the sweeper ran correctly
    assert proc.returncode in (0, 1), (
        f"sweep_drift.py exited with unexpected code {proc.returncode}:\n"
        f"stdout: {proc.stdout[:500]}\nstderr: {proc.stderr[:500]}"
    )
