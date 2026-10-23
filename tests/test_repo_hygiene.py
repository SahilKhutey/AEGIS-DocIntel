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


@pytest.mark.skipif(shutil.which("git") is None or not (ROOT / ".git").exists(), reason="not a git checkout")
def test_root_directory_clean_structure():
    """Verify repository root is clean: no loose screenshots, scratch directory, or misplaced artifacts."""
    tracked_root_files = [f for f in _git("ls-files").stdout.splitlines() if "/" not in f]
    
    # Assert no loose screenshots in root
    png_in_root = [f for f in tracked_root_files if f.endswith(".png")]
    assert not png_in_root, f"Screenshots must be placed in docs/assets/screenshots, found in root: {png_in_root}"
    
    # Assert scratch directory is not tracked in git
    tracked_scratch = [f for f in _git("ls-files", "scratch").stdout.splitlines()]
    assert not tracked_scratch, f"Scratch directory should not be tracked in git: {tracked_scratch}"
    
    # Assert specifications and reports directories exist and contain files
    specs_dir = ROOT / "docs" / "specifications"
    reports_dir = ROOT / "docs" / "reports"
    assert specs_dir.is_dir() and any(specs_dir.glob("*.md")), "docs/specifications should exist and contain markdown files"
    assert reports_dir.is_dir() and any(reports_dir.glob("*.md")), "docs/reports should exist and contain markdown files"
