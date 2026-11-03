"""
aegis/audit/runner/planner.py
=============================
Generates a validated execution plan from configuration and registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from aegis.audit.runner.exceptions import SuiteNotFoundError
from aegis.audit.runner.registry import AuditRegistry
from aegis.audit.suites.base import BaseAuditSuite


@dataclass
class PlannedSuite:
    suite_id: str
    suite: BaseAuditSuite
    enabled: bool = True
    required: bool = True
    timeout_seconds: float = 180.0
    dependencies: List[str] = field(default_factory=list)


class AuditPlanner:
    """Builds and validates execution plans for audit runs."""

    @classmethod
    def build_plan(
        cls,
        config: Dict[str, Any],
        registry: AuditRegistry,
        requested_suites: Optional[List[str]] = None,
        all_flag: bool = False,
    ) -> List[PlannedSuite]:
        audit_cfg = config.get("audit", {})
        exec_cfg = audit_cfg.get("execution", {})
        default_suite_timeout = float(exec_cfg.get("suite_timeout_seconds", 180.0))
        configured_suites = audit_cfg.get("suites", [])

        # Create lookup of configured settings
        cfg_map = {s["id"].lower(): s for s in configured_suites if "id" in s}

        planned: List[PlannedSuite] = []

        if requested_suites:
            # Specific suites requested via CLI
            for req_id in requested_suites:
                norm_req = req_id.strip().lower()
                if not registry.has(norm_req):
                    raise SuiteNotFoundError(f"Requested audit suite not registered: '{req_id}'")

                suite = registry.get(norm_req)
                s_cfg = cfg_map.get(norm_req, {})
                planned.append(PlannedSuite(
                    suite_id=suite.suite_id,
                    suite=suite,
                    enabled=s_cfg.get("enabled", True),
                    required=s_cfg.get("required", True),
                    timeout_seconds=float(s_cfg.get("timeout_seconds", default_suite_timeout)),
                    dependencies=s_cfg.get("dependencies", []),
                ))
        else:
            # Plan from configuration or all registered suites
            if configured_suites and not all_flag:
                for s_cfg in configured_suites:
                    s_id = s_cfg.get("id", "").strip().lower()
                    if not s_id:
                        continue
                    if not registry.has(s_id):
                        if s_cfg.get("required", False):
                            raise SuiteNotFoundError(
                                f"Required suite from configuration not registered: '{s_id}'"
                            )
                        continue
                    suite = registry.get(s_id)
                    planned.append(PlannedSuite(
                        suite_id=suite.suite_id,
                        suite=suite,
                        enabled=s_cfg.get("enabled", True),
                        required=s_cfg.get("required", True),
                        timeout_seconds=float(s_cfg.get("timeout_seconds", default_suite_timeout)),
                        dependencies=s_cfg.get("dependencies", []),
                    ))
            else:
                # All registered suites
                for norm_id, suite in registry.get_all().items():
                    s_cfg = cfg_map.get(norm_id, {})
                    planned.append(PlannedSuite(
                        suite_id=suite.suite_id,
                        suite=suite,
                        enabled=s_cfg.get("enabled", True),
                        required=s_cfg.get("required", False),
                        timeout_seconds=float(s_cfg.get("timeout_seconds", default_suite_timeout)),
                        dependencies=s_cfg.get("dependencies", []),
                    ))

        return planned
