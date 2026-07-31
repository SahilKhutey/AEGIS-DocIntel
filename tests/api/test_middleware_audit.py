"""Audit records appended per request."""

from __future__ import annotations

from pathlib import Path

from amdi.api.middleware.audit import audit
from amdi.security.audit import verify_file


def test_audit_writes_to_storage(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "filesystem")
    monkeypatch.setenv("AMDI_STORAGE_ROOT", str(tmp_path))
    from amdi.config import get_settings
    get_settings.cache_clear()
    audit("doc.upload", resource="d-1", outcome="ok", actor="u-1")
    audit("doc.delete", resource="d-1", outcome="denied",
          code="FORBIDDEN", actor="u-1")
    log = next(Path(tmp_path / "audit").glob("audit-*.log"))
    ok, n = verify_file(log)
    assert ok and n == 2
