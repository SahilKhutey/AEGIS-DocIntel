"""Hash-chained audit: tamper detection."""

from __future__ import annotations

import json
import time
from pathlib import Path

from amdi.security.audit import AuditChain, AuditRecord, verify_file


def test_chain_links_records(tmp_path: Path) -> None:
    chain = AuditChain(backend="file", sink_path=tmp_path)
    chain.append(AuditRecord(ts=int(time.time() * 1000),
                             actor="u1", action="upload",
                             resource="doc-1", outcome="ok"))
    chain.append(AuditRecord(ts=int(time.time() * 1000),
                             actor="u2", action="delete",
                             resource="doc-1", outcome="ok"))
    log = next(tmp_path.glob("audit-*.log"))
    assert verify_file(log)[0] is True


def test_chain_detects_tamper(tmp_path: Path) -> None:
    chain = AuditChain(backend="file", sink_path=tmp_path)
    chain.append(AuditRecord(ts=1, actor="u1", action="upload",
                             resource="d-1", outcome="ok"))
    chain.append(AuditRecord(ts=2, actor="u2", action="delete",
                             resource="d-1", outcome="ok"))
    log = next(tmp_path.glob("audit-*.log"))

    lines = log.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[0])
    rec["actor"] = "evil"
    lines[0] = json.dumps(rec)
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")

    ok, n = verify_file(log)
    assert ok is False
    assert n == 0
