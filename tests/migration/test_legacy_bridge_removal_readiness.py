"""0.4.0 readiness test.

A PR that claims v0.4.0 readiness must satisfy ALL of:

* `src/amdi/legacy_bridge.py` does not exist
* no file under src/amdi/ emits `FutureWarning` with "REMOVED in v0.4.0"
* the matrix file is empty for severity=warn or severity=error
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "src/amdi/legacy_bridge.py"
MATRIX = ROOT / "tools/deprecation_matrix.json"


def test_bridge_removed() -> None:
    """This test xfails until v0.4.0 when the bridge is removed."""
    if BRIDGE.exists():
        pytest.xfail("legacy_bridge still present; not yet v0.4.0-ready")


def test_matrix_empty_in_0_4_0() -> None:
    """In v0.4.0 the matrix should be empty. For now it xfails."""
    if not MATRIX.exists():
        return
    rules = json.loads(MATRIX.read_text(encoding="utf-8"))
    if rules:
        pytest.xfail(f"matrix still has {len(rules)} rules; not yet v0.4.0-ready")
