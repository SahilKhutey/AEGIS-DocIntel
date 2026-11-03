"""
aegis/audit/traceability/environment_collector.py
=================================================
Captures environment runtime metadata and dependency lock digests.
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict
from aegis.audit.evidence.hashing import hash_file


class EnvironmentCollector:
    """Collects runtime environment metadata safely."""

    @classmethod
    def collect(cls, root_dir: Path | None = None) -> Dict[str, Any]:
        if root_dir is None:
            root_dir = Path(__file__).resolve().parent.parent.parent.parent

        lock_hash = "UNLOCKED"
        core_lock = root_dir / "requirements-core.lock.txt"
        if core_lock.is_file():
            try:
                lock_hash = hash_file(core_lock)
            except Exception:
                pass

        return {
            "os": platform.system(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "runner_version": "1.0.0",
            "dependency_lock_hash": lock_hash,
            "platform_identifier": platform.platform(),
        }
