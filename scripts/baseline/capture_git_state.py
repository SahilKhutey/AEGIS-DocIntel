#!/usr/bin/env python3
"""
scripts/baseline/capture_git_state.py
=====================================
Captures the canonical Git baseline state for WP01-01.
Deterministic, reproducible, and read-only with respect to git history.
"""

from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE_DIR = ROOT / "audit" / "baseline"
BASELINE_DIR.mkdir(parents=True, exist_ok=True)


def run_git(args: list[str]) -> str:
    res = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True, check=True)
    return res.stdout.strip()


def main() -> int:
    try:
        head_commit = run_git(["rev-parse", "HEAD"])
        master_commit = run_git(["rev-parse", "master"])
        main_commit = run_git(["rev-parse", "main"])
        active_branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        remote_url = run_git(["remote", "get-url", "origin"])
        status_porcelain = run_git(["status", "--porcelain"])
        
        # Check diff between master and main
        diff_master_main = run_git(["diff", "master..main"])
        comparison_status = "ALIGNED_ZERO_DIFF" if not diff_master_main else "DIVERGENT"

        working_tree = "CLEAN" if not status_porcelain else "MODIFIED"

        manifest = {
            "baseline_id": "AEGIS-BASELINE-001",
            "project": "AEGIS-DocIntel",
            "canonical_branch": "master",
            "canonical_commit": master_commit,
            "head_commit": head_commit,
            "active_branch": active_branch,
            "comparison_branch": "main",
            "comparison_commit": main_commit,
            "comparison_status": comparison_status,
            "working_tree": working_tree,
            "remote_origin": remote_url,
            "baseline_tag": "aegis-baseline-001",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "FROZEN"
        }

        manifest_path = BASELINE_DIR / "baseline_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"[OK] Wrote baseline manifest: {manifest_path}")

        # Text files
        (BASELINE_DIR / "canonical_commit.txt").write_text(master_commit + "\n", encoding="utf-8")
        
        summary = run_git(["show", "--stat", "--oneline", master_commit])
        (BASELINE_DIR / "canonical_commit_summary.txt").write_text(summary + "\n", encoding="utf-8")
        print("[OK] Wrote canonical commit text references")

        return 0
    except Exception as e:
        print(f"[ERROR] Failed to capture git state: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
