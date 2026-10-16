"""Repository hygiene guards (skipped outside a git checkout)."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


@pytest.mark.skipif(shutil.which("git") is None or not (ROOT / ".git").exists(), reason="not a git checkout")
def test_no_database_files_are_tracked():
    """data/annotations.db was force-added despite '*.db' in .gitignore; the app and the test suite write to it,
    so every test run dirtied the tree (11 churn commits)."""
    tracked = [f for f in _git("ls-files").stdout.splitlines()
               if f.endswith((".db", ".sqlite", ".sqlite3")) and not f.startswith(("_archive/", "tests/fixtures/"))]
    assert not tracked, f"runtime state must not be committed: {tracked}"


def test_gitignore_covers_runtime_databases():
    text = (ROOT / ".gitignore").read_text()
    assert "data/*.db" in text


def test_gitleaks_allowlist_entries_are_documented():
    """Every allowlisted fingerprint must be preceded by an explanatory comment (never a silent suppression)."""
    lines = (ROOT / ".gitleaksignore").read_text().splitlines()
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith("#"):
            assert any(l.startswith("#") for l in lines[:i]), f"undocumented allowlist entry: {line}"
