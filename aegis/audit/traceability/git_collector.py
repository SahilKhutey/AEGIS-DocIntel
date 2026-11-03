"""
aegis/audit/traceability/git_collector.py
=========================================
Captures Git commit SHA, branch, remote identity, and working-tree cleanliness.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional
from aegis.audit.runner.exceptions import ProvenanceError


class GitCollector:
    """Collects Git state securely and nondestructively."""

    def __init__(self, repo_path: str | Path = ".") -> None:
        self.repo_path = Path(repo_path).resolve()

    def _run_git(self, *args: str) -> str:
        try:
            res = subprocess.run(
                ["git", *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=15,
            )
            return res.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise ProvenanceError(f"Git command failed ('git {' '.join(args)}'): {e.stderr.strip()}")
        except FileNotFoundError:
            raise ProvenanceError("Git executable not found in PATH")
        except Exception as e:
            raise ProvenanceError(f"Error executing git: {e}")

    def collect(self) -> Dict[str, Any]:
        # Verify it is inside a git work tree
        try:
            is_work_tree = self._run_git("rev-parse", "--is-inside-work-tree")
            if is_work_tree != "true":
                raise ProvenanceError(f"Directory is not a git repository: {self.repo_path}")
        except ProvenanceError:
            raise

        commit_sha = self._run_git("rev-parse", "--verify", "HEAD")
        
        # Branch or detached HEAD
        try:
            branch = self._run_git("symbolic-ref", "--short", "-q", "HEAD")
        except ProvenanceError:
            branch = None  # Detached HEAD

        # Remote origin URL (sanitizing credentials)
        remote_url = ""
        try:
            raw_remote = self._run_git("remote", "get-url", "origin")
            # Strip username:password from https://user:pass@host/...
            remote_url = re.sub(r"https?://([^@]+)@", "https://", raw_remote)
        except ProvenanceError:
            pass

        # Commit timestamp
        commit_ts = ""
        try:
            commit_ts = self._run_git("log", "-1", "--format=%cI")
        except ProvenanceError:
            pass

        # Status inspection (porcelain)
        status_out = self._run_git("status", "--porcelain=v1")
        modified_count = 0
        untracked_count = 0

        for line in status_out.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("??"):
                untracked_count += 1
            else:
                modified_count += 1

        is_clean = (modified_count == 0 and untracked_count == 0)

        return {
            "repository": self.repo_path.name,
            "remote_url": remote_url,
            "branch": branch,
            "commit_sha": commit_sha,
            "commit_timestamp": commit_ts,
            "working_tree_clean": is_clean,
            "modified_files_count": modified_count,
            "untracked_files_count": untracked_count,
        }
