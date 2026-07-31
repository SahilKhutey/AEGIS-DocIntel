"""Migration script exits 0 against this checkout."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def test_verify_migration_passes() -> None:
    res = subprocess.run(
        [sys.executable, "scripts/verify_migration.py"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert res.returncode == 0, res.stderr or res.stdout
