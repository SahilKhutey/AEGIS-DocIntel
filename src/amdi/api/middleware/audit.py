"""Audit middleware: appends one record per authenticated request."""

from __future__ import annotations

import time
from pathlib import Path

from amdi.config import get_settings
from amdi.security.audit import AuditChain, AuditRecord

_chain: AuditChain | None = None


def _chain_singleton() -> AuditChain:
    global _chain
    if _chain is None:
        s = get_settings()
        _chain = AuditChain(
            backend=s.audit_backend,
            root=Path(s.storage_root),
        )
    return _chain


def audit(action: str, *, resource: str, outcome: str,
          code: str = "", detail: str = "", actor: str = "anonymous") -> None:
    rec = AuditRecord(
        ts=int(time.time() * 1000),
        actor=actor,
        action=action,
        resource=resource,
        outcome=outcome,
        code=code,
        detail=detail[:512],
    )
    _chain_singleton().append(rec)


__all__ = ["audit"]
