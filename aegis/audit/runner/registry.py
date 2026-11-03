"""
aegis/audit/runner/registry.py
==============================
Registry managing registered audit suites.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from aegis.audit.runner.exceptions import DuplicateSuiteError, SuiteNotFoundError
from aegis.audit.suites.base import BaseAuditSuite


class AuditRegistry:
    """Central registry of executable audit suites."""

    def __init__(self) -> None:
        self._suites: Dict[str, BaseAuditSuite] = {}

    def register(self, suite: BaseAuditSuite) -> None:
        """Register an audit suite instance."""
        if not isinstance(suite, BaseAuditSuite):
            raise TypeError(f"Suite must inherit from BaseAuditSuite, got {type(suite).__name__}")
        
        suite_id = suite.suite_id.strip() if suite.suite_id else ""
        if not suite_id:
            raise ValueError("Suite ID is required and cannot be empty")

        norm_id = suite_id.lower()
        if norm_id in self._suites:
            raise DuplicateSuiteError(f"Duplicate audit suite identifier: '{suite_id}'")

        self._suites[norm_id] = suite

    def get(self, suite_id: str) -> BaseAuditSuite:
        """Retrieve a registered suite by ID (case-insensitive)."""
        norm_id = suite_id.strip().lower()
        if norm_id not in self._suites:
            raise SuiteNotFoundError(f"Audit suite not found: '{suite_id}'")
        return self._suites[norm_id]

    def has(self, suite_id: str) -> bool:
        """Check if a suite is registered."""
        return suite_id.strip().lower() in self._suites

    def list_suites(self) -> List[str]:
        """Return all registered suite IDs."""
        return [s.suite_id for s in self._suites.values()]

    def get_all(self) -> Dict[str, BaseAuditSuite]:
        """Return mapping of norm_id to suite instance."""
        return dict(self._suites)

    def clear(self) -> None:
        """Clear all registered suites."""
        self._suites.clear()
