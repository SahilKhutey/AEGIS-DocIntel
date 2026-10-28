"""
src/services/health_service.py
==============================
AEGIS-DocIntel — Health & Readiness Inspection Service.
Executes non-disclosing dependency and storage liveness checks.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, Optional, Tuple


class HealthService:
    """Service providing liveness and readiness diagnostic inspections."""

    def __init__(self, container: Optional[Any] = None) -> None:
        self.container = container

    def check_liveness(self) -> Dict[str, str]:
        """
        Liveness probe: verifies application process is active.
        Strict invariant: Never call external databases or model providers here.
        """
        return {"status": "ok"}

    async def check_readiness(self) -> Tuple[bool, Dict[str, str]]:
        """
        Readiness probe: verifies persistent storage and dependencies can accept traffic.
        Returns (is_ready, dependency_states).
        Strict invariant: Never disclose internal paths, hostnames, or credentials.
        """
        states: Dict[str, str] = {
            "api": "ok",
            "database": "unknown",
            "memory": "ok",
        }

        if self.container is None:
            states["container"] = "missing"
            states["database"] = "unavailable"
            return False, states

        # 1. Container readiness
        if hasattr(self.container, "verify_readiness"):
            try:
                is_ready, details = await self.container.verify_readiness()
                # Coarsen and sanitize states to avoid information disclosure
                for k, v in details.items():
                    states[k] = "ok" if v == "ok" else "unavailable"
                return is_ready, states
            except Exception:
                states["database"] = "unavailable"
                return False, states

        # 2. Standalone database inspection fallback
        doc_service = getattr(self.container, "document_service", None)
        db_path = getattr(doc_service, "db_path", None) if doc_service else None
        if db_path and db_path != ":memory:":
            try:
                with sqlite3.connect(db_path, timeout=2.0) as conn:
                    conn.execute("SELECT 1 FROM documents LIMIT 1")
                states["database"] = "ok"
            except Exception:
                states["database"] = "unavailable"
                return False, states
        else:
            states["database"] = "ok"

        return True, states
