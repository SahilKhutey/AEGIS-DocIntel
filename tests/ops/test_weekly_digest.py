"""weekly_digest.py composes the digest from existing artefacts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_digest_writes_artifact(tmp_path: Path) -> None:
    out_dir = ROOT / "release" / "v0.3.0-week1"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Ensure TRIAGE_LOG and DECISIONS exist for the digest
    triage = out_dir / "TRIAGE_LOG.md"
    decisions = out_dir / "DECISIONS.md"
    if not triage.exists():
        triage.write_text("## by severity\ntable ...", encoding="utf-8")
    if not decisions.exists():
        decisions.write_text("## D-17 ...", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "weekly_digest.py"),
         "--week-start", "2026-10-05"],
        capture_output=True, text=True, cwd=ROOT
    )
    assert res.returncode == 0, f"stderr: {res.stderr[:500]}"
    assert "Weekly digest" in res.stdout
