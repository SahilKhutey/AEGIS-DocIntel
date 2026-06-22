"""
Tenant Context
================

Per-request tenant isolation via contextvars.
"""

from __future__ import annotations

import threading
from contextvars import ContextVar
from typing import Any, Dict, Optional

_current_tenant_id: ContextVar[Optional[str]] = ContextVar(
    "current_tenant_id", default=None
)
_current_tenant_config: ContextVar[Dict[str, Any]] = ContextVar(
    "current_tenant_config", default={}
)


class TenantContext:
    """Thread-safe + async-safe tenant context manager."""

    def __init__(self, tenant_id: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.tenant_id = tenant_id
        self.config = config or {}
        self._token_tenant: Optional[Any] = None
        self._token_config: Optional[Any] = None

    def __enter__(self):
        self._token_tenant = _current_tenant_id.set(self.tenant_id)
        self._token_config = _current_tenant_config.set(self.config)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token_tenant is not None:
            _current_tenant_id.reset(self._token_tenant)
        if self._token_config is not None:
            _current_tenant_config.reset(self._token_config)

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


def set_current_tenant(tenant_id: str, config: Optional[Dict[str, Any]] = None) -> TenantContext:
    """Set the current tenant context (returns context manager)."""
    return TenantContext(tenant_id, config)


def get_current_tenant() -> Optional[str]:
    """Get the current tenant ID."""
    return _current_tenant_id.get()


def get_current_tenant_config() -> Dict[str, Any]:
    """Get the current tenant config."""
    return _current_tenant_config.get()
