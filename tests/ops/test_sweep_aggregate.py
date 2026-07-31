"""sweep_aggregate.py renders weekly markdown summaries."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _write_sweep(d: Path, kind: str, ts: str, ok: bool) -> None:
    d.mkdir(parents=True, exist_ok=True)
    safe_ts = ts.replace(":", "-")
    (d / f"{safe_ts}-{kind}.json").write_text(
        json.dumps({"kind": kind, "ts": ts, "ok": ok}), encoding="utf-8",
    )


def test_renders_all_kinds(tmp_path: Path, monkeypatch) -> None:
    import scripts.sweep_aggregate as mod
    monkeypatch.setattr(mod, "SWEEPS", tmp_path)
    for k in ("drift", "openapi_sync", "audit_integrity", "deps"):
        _write_sweep(tmp_path, k, "2026-09-30T06:00:00", True)
        _write_sweep(tmp_path, k, "2026-10-01T06:00:00", True)
    week = mod.load_week(dt.date(2026, 9, 28))
    md = mod.render_md(week)
    assert "drift" in md and "deps" in md
