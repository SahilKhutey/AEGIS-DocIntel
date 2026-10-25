"""pyproject.toml is the single source of truth for dependencies; requirements-*.txt are generated mirrors.

Regression for: hypothesis declared in pyproject but missing from requirements-dev.txt, and python-docx /
python-pptx / openpyxl declared nowhere — so the documented install aborted with zero tests run.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(*args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "check_dependency_sync.py"), *args],
                          capture_output=True, text=True, cwd=ROOT)


def test_requirements_files_match_pyproject():
    r = _run()
    assert r.returncode == 0, r.stdout + r.stderr


def test_test_time_dependencies_are_declared():
    """Anything the suite imports at collection time must be installable from requirements-dev/core."""
    core = (ROOT / "requirements-core.txt").read_text().lower()
    dev = (ROOT / "requirements-dev.txt").read_text().lower()
    for pkg in ("python-docx", "python-pptx", "openpyxl"):
        assert pkg in core, f"{pkg} is imported by the DOCX/PPTX/XLSX loaders but not in requirements-core.txt"
    assert "hypothesis" in dev, "hypothesis is imported by tests/test_theorem_properties.py"
    assert "pytest-asyncio" in dev
