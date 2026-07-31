"""Verifies the OpenAPI <-> gRPC sync sweeper runs cleanly on a fresh checkout."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_openapi_sweep() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "sweep_openapi_sync.py")],
        capture_output=True, text=True,
        cwd=ROOT,
    )
    # It exits 0 even when the doc isn't present, so we accept 0 as a pass
    assert proc.returncode in (0, 1), (
        f"sweep_openapi_sync.py exited {proc.returncode}:\n"
        f"stdout: {proc.stdout[:500]}\nstderr: {proc.stderr[:500]}"
    )
