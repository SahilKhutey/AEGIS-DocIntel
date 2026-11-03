"""
aegis/audit/suites/base.py
==========================
Abstract base contract for all AEGIS audit suites.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAuditSuite(ABC):
    """
    Standard contract for all audit suites.
    Every suite must expose a unique identifier, version, validation, execution,
    and cleanup hooks.
    """

    suite_id: str = ""
    suite_name: str = ""
    suite_version: str = "1.0.0"
    description: str = ""
    tags: List[str] = []

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    @abstractmethod
    def validate(self, context: Any) -> None:
        """
        Validate suite prerequisites, environment dependencies, and tools.
        Raises SuiteValidationError or AuditError if prerequisites are missing.
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, context: Any) -> Dict[str, Any]:
        """
        Execute the audit suite and return structured results.
        Must return a dictionary containing at least:
        - status: str ("PASSED", "FAILED", etc.)
        - statistics: dict (total, passed, failed, skipped, errors)
        - findings: list[dict]
        - artifacts: list[dict]
        """
        raise NotImplementedError

    def cleanup(self, context: Any) -> None:
        """
        Release any temporary files, connections, or resources allocated.
        Must be guaranteed to run even if validate or execute raises an exception.
        """
        pass
