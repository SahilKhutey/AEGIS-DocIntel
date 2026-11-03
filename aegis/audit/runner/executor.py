"""
aegis/audit/runner/executor.py
==============================
Execution engine that runs planned audit suites with timeout limits,
exception handling, and guaranteed cleanup.
"""

from __future__ import annotations

import datetime
import time
from typing import Any, Dict, List, Optional
from aegis.audit.runner.exceptions import (
    SuiteExecutionError,
    SuiteValidationError,
    TimeoutException,
)
from aegis.audit.runner.planner import PlannedSuite
from aegis.audit.runner.result_normalizer import AuditResultNormalizer
from aegis.audit.runner.timeout_manager import TimeoutManager


class AuditExecutor:
    """Executes planned suites against an audit run context."""

    def __init__(self, fail_fast: bool = False) -> None:
        self.fail_fast = fail_fast

    def execute_suite(self, planned: PlannedSuite, context: Any) -> Dict[str, Any]:
        suite = planned.suite
        suite_id = planned.suite_id
        suite_version = getattr(suite, "suite_version", "1.0.0")

        if not planned.enabled:
            return AuditResultNormalizer.normalize(
                suite_id=suite_id,
                suite_version=suite_version,
                status="SKIPPED",
            )

        started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        t0 = time.monotonic()
        status = "PASSED"
        raw_result: Dict[str, Any] = {}
        error_type: Optional[str] = None
        error_message: Optional[str] = None

        try:
            # 1. Validation hook
            suite.validate(context)

            # 2. Execution with timeout ceiling
            raw_result = TimeoutManager.execute(
                suite.execute,
                args=(context,),
                timeout_seconds=planned.timeout_seconds,
            )
            status = raw_result.get("status", "PASSED")

        except SuiteValidationError as e:
            status = "BLOCKED"
            error_type = type(e).__name__
            error_message = str(e)

        except TimeoutException as e:
            status = "TIMEOUT"
            error_type = type(e).__name__
            error_message = str(e)

        except Exception as e:
            status = "ERROR"
            error_type = type(e).__name__
            error_message = str(e)

        finally:
            # 3. Guaranteed cleanup
            try:
                suite.cleanup(context)
            except Exception as cleanup_exc:
                if hasattr(context, "record_cleanup_error"):
                    context.record_cleanup_error(suite_id, cleanup_exc)

        duration = time.monotonic() - t0
        completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return AuditResultNormalizer.normalize(
            suite_id=suite_id,
            suite_version=suite_version,
            raw_result=raw_result,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            error_type=error_type,
            error_message=error_message,
        )

    def execute_plan(
        self,
        plan: List[PlannedSuite],
        context: Any,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        for planned in plan:
            res = self.execute_suite(planned, context)
            results.append(res)

            if self.fail_fast and res["status"] in {"FAILED", "ERROR", "TIMEOUT"}:
                break

        return results
