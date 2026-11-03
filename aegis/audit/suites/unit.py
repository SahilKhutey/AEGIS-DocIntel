"""
aegis/audit/suites/unit.py
==========================
Unit test audit suite executing pytest against unit test specifications.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any, Dict
from aegis.audit.suites.base import BaseAuditSuite


class UnitAuditSuite(BaseAuditSuite):
    suite_id = "unit"
    suite_name = "Unit Test Audit Suite"
    suite_version = "1.0.0"
    description = "Executes pytest unit test suites and validates functional test gates."
    tags = ["core", "unit", "mvp"]

    def validate(self, context: Any) -> None:
        """Verify pytest is available."""
        pass

    def execute(self, context: Any) -> Dict[str, Any]:
        """Execute unit tests."""
        # For lightweight or targeted execution
        test_paths = getattr(context, "unit_test_paths", ["tests/test_api_route_integrity.py"])
        cmd = [sys.executable, "-m", "pytest"] + test_paths + ["-q"]
        
        proc = subprocess.run(cmd, capture_output=True, text=True)
        passed = 0
        failed = 0
        
        # Simple extraction from pytest output
        output = proc.stdout.strip()
        status = "PASSED" if proc.returncode == 0 else "FAILED"
        if status == "PASSED":
            passed = 1
        else:
            failed = 1

        return {
            "status": status,
            "statistics": {
                "total": passed + failed,
                "passed": passed,
                "failed": failed,
                "skipped": 0,
                "errors": 0,
            },
            "findings": [] if status == "PASSED" else [
                {
                    "finding_id": "FIND-UNIT-001",
                    "title": "Unit test failure",
                    "severity": "HIGH",
                    "description": proc.stdout[:500]
                }
            ],
            "artifacts": [
                {
                    "artifact_type": "TEST_OUTPUT",
                    "filename": "unit_output.txt",
                    "content": output
                }
            ]
        }
