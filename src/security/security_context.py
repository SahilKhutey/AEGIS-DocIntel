"""
AEGIS-DocIntel Request Security Context (PROT-04 WP-04.08)
Maintains thread-safe request correlation, lineage, and tenant identity.
"""

from __future__ import annotations

import contextvars
from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4


@dataclass
class SecurityContext:
    request_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    tenant_id: Optional[str] = None
    evaluator_id: Optional[str] = None
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    source_ip: str = "127.0.0.1"
    is_admin: bool = False


_context_var: contextvars.ContextVar[Optional[SecurityContext]] = contextvars.ContextVar(
    "aegis_security_context", default=None
)


def get_current_security_context() -> SecurityContext:
    ctx = _context_var.get()
    if ctx is None:
        ctx = SecurityContext()
        _context_var.set(ctx)
    return ctx


def set_current_security_context(ctx: SecurityContext) -> contextvars.Token:
    return _context_var.set(ctx)


def reset_security_context(token: contextvars.Token) -> None:
    _context_var.reset(token)
