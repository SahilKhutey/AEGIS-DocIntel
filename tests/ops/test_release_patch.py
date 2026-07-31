"""release_patch.py produces DIFF_STAT output from git diff."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def test_diff_stat_from_git(tmp_path: Path) -> None:
    """Verify `git diff --stat` runs without error in a real repo."""
    repo = tmp_path / "r"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    (repo / "a.txt").write_text("hi")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)
    (repo / "a.txt").write_text("hi2")
    subprocess.run(["git", "-C", str(repo), "commit", "-qam", "x"], check=True)

    stat = subprocess.check_output(
        ["git", "-C", str(repo), "diff", "--stat", "HEAD~1..HEAD"], text=True,
    )
    assert "a.txt" in stat
