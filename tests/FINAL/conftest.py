"""Common fixtures for the final acceptance tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys_path = ROOT / "src"
os.environ.setdefault("AMDI_STORAGE_BACKEND", "memory")
os.environ.setdefault("AMDI_QUEUE_BACKEND", "memory")
os.environ.setdefault("AMDI_JWT_SECRET", "test-secret-with-enough-entropy-1234")

sys.path.insert(0, str(sys_path))


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT
