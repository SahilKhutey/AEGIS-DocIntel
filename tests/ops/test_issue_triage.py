"""issue_triage.py classifies payloads into labels + severity."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _run(payload: dict) -> dict:
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "issue_triage.py")],
        input=json.dumps(payload), text=True, capture_output=True,
        cwd=ROOT,
    )
    return json.loads(p.stdout)


def test_outage_is_sev1() -> None:
    out = _run({"title": "outage in our cluster",
                 "body": "data loss, see trace"})
    assert out["severity"] == "Sev-1"


def test_perf_label_picked() -> None:
    out = _run({"title": "upload is slow under load",
                 "body": "p95 latency 3s"})
    assert "K-perf" in out["labels"]


def test_sev3_cosmetic() -> None:
    out = _run({"title": "typo in README",
                 "body": "minor nit"})
    assert out["severity"] == "Sev-3"
