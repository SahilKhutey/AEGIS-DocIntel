"""
Release Engineering Test Suite — Client Distribution Boundary (REL-004, REL-005, GATE-07, GATE-08)
PROT-FINAL-04: Workstream REL-01
"""

from __future__ import annotations

import zipfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ARCHIVE_PATH = REPO_ROOT / "release" / "client" / "AEGIS-DocIntel-Demo-Edition.zip"
REPORT_PATH = REPO_ROOT / "release" / "reports" / "artifact-boundary-report.json"

PROHIBITED_EXTENSIONS = {".py", ".pyc", ".pyo", ".pyd", ".map", ".key"}
FORBIDDEN_MARKERS = [
    "BEGIN PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN EC PRIVATE KEY",
    "sk-",
    "ghp_",
    "AKIA",
    "postgresql://",
]


def test_rel_001_archive_exists_and_valid():
    """REL-001: Verifies that the client release archive exists and is a valid zip."""
    assert ARCHIVE_PATH.exists(), f"Release archive missing: {ARCHIVE_PATH}"
    assert zipfile.is_zipfile(ARCHIVE_PATH), "Archive is not a valid zip file"
    assert ARCHIVE_PATH.stat().st_size > 10000, "Archive size unreasonably small"


def test_rel_002_zero_python_or_engine_code_in_archive():
    """REL-005: Verifies zero Python engine source files, bytecode, or DAG engines are in the client archive."""
    with zipfile.ZipFile(ARCHIVE_PATH, "r") as zf:
        for name in zf.namelist():
            p = Path(name)
            assert p.suffix.lower() not in PROHIBITED_EXTENSIONS, f"Prohibited extension '{p.suffix}' in archive: {name}"
            assert "src/core" not in name, f"Private core engine directory leaked: {name}"
            assert "src/api" not in name, f"Private backend API directory leaked: {name}"
            assert "evaluation/" not in name, f"Private evaluation benchmark leaked: {name}"


def test_rel_003_zero_secrets_or_private_keys_in_archive():
    """REL-004: Verifies zero private keys, API keys, database credentials, or .env files are in archive."""
    with zipfile.ZipFile(ARCHIVE_PATH, "r") as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            assert not Path(name).name.startswith(".env"), f"Prohibited .env file in archive: {name}"
            text = zf.read(name).decode("utf-8", errors="ignore")
            for marker in FORBIDDEN_MARKERS:
                assert marker not in text, f"Forbidden secret marker '{marker}' found in archive file: {name}"


def test_rel_004_boundary_report_verification():
    """GATE-07: Verifies that the automated boundary validation report confirms COMPLIANT status."""
    assert REPORT_PATH.exists(), f"Boundary report missing: {REPORT_PATH}"
    import json
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    assert report.get("status") == "COMPLIANT"
    assert report.get("violations_count") == 0
    assert report.get("total_files_scanned") >= 37
