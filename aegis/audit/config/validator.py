"""
aegis/audit/config/validator.py
==============================
Validates configuration contracts structurally, semantically (CFG-001..010),
and operationally.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from aegis.audit.config.fingerprint import compute_configuration_hash
from aegis.audit.runner.exceptions import ConfigurationError
from aegis.audit.runner.registry import AuditRegistry


class AuditConfigValidator:
    """Multi-tier configuration validation engine."""

    SUPPORTED_VERSIONS = {"1.0", "1.0.0"}

    @classmethod
    def validate(
        cls,
        config: Dict[str, Any],
        registry: Optional[AuditRegistry] = None,
        base_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        errors: List[Dict[str, str]] = []
        warnings: List[Dict[str, str]] = []

        # 1. Structural Validation
        schema_status = "PASS"
        if not isinstance(config, dict):
            return {
                "configuration_status": "INVALID",
                "schema_validation": "FAIL",
                "semantic_validation": "NOT_RUN",
                "operational_validation": "NOT_RUN",
                "configuration_hash": "",
                "errors": [{"code": "CFG-STRUCT", "field": "root", "message": "Configuration root must be an object"}],
                "warnings": []
            }

        version = config.get("version")
        if not version or str(version) not in cls.SUPPORTED_VERSIONS:
            errors.append({
                "code": "CFG-001",
                "field": "version",
                "message": f"Unsupported configuration version: '{version}'. Supported: {cls.SUPPORTED_VERSIONS}"
            })
            schema_status = "FAIL"

        audit = config.get("audit")
        if not isinstance(audit, dict):
            errors.append({
                "code": "CFG-STRUCT",
                "field": "audit",
                "message": "Missing or invalid 'audit' object"
            })
            schema_status = "FAIL"
            return {
                "configuration_status": "INVALID",
                "schema_validation": "FAIL",
                "semantic_validation": "NOT_RUN",
                "operational_validation": "NOT_RUN",
                "configuration_hash": "",
                "errors": errors,
                "warnings": warnings
            }

        # Check required fields inside audit
        for req in ["name", "enabled", "execution", "suites", "evidence"]:
            if req not in audit:
                errors.append({
                    "code": "CFG-STRUCT",
                    "field": f"audit.{req}",
                    "message": f"Required configuration key missing: 'audit.{req}'"
                })
                schema_status = "FAIL"

        # 2. Semantic Validation
        semantic_status = "PASS"
        execution = audit.get("execution", {})
        timeout = execution.get("timeout_seconds")
        if timeout is not None and (not isinstance(timeout, (int, float)) or timeout <= 0):
            errors.append({
                "code": "CFG-004",
                "field": "audit.execution.timeout_seconds",
                "message": "Execution timeout_seconds must be a positive number"
            })
            semantic_status = "FAIL"

        retries = execution.get("retries", 0)
        if not isinstance(retries, int) or retries < 0 or retries > 5:
            errors.append({
                "code": "CFG-005",
                "field": "audit.execution.retries",
                "message": "Retries must be an integer between 0 and 5"
            })
            semantic_status = "FAIL"

        parallel = execution.get("max_parallel_suites", 1)
        if not isinstance(parallel, int) or parallel < 1:
            errors.append({
                "code": "CFG-006",
                "field": "audit.execution.max_parallel_suites",
                "message": "max_parallel_suites must be an integer >= 1"
            })
            semantic_status = "FAIL"

        is_strict = bool(execution.get("strict", False))

        # Suites semantic checks
        suites = audit.get("suites", [])
        if not isinstance(suites, list) or len(suites) == 0:
            errors.append({
                "code": "CFG-STRUCT",
                "field": "audit.suites",
                "message": "audit.suites must be a non-empty list"
            })
            semantic_status = "FAIL"
        else:
            seen_ids = set()
            for idx, s in enumerate(suites):
                if not isinstance(s, dict) or "id" not in s:
                    errors.append({
                        "code": "CFG-STRUCT",
                        "field": f"audit.suites[{idx}]",
                        "message": "Each suite declaration must have an 'id'"
                    })
                    semantic_status = "FAIL"
                    continue

                sid = str(s["id"]).strip().lower()
                # CFG-002: unique suite IDs
                if sid in seen_ids:
                    errors.append({
                        "code": "CFG-002",
                        "field": f"audit.suites[{idx}].id",
                        "message": f"Duplicate suite id in configuration: '{sid}'"
                    })
                    semantic_status = "FAIL"
                seen_ids.add(sid)

                # CFG-003: suite registered check
                if registry and not registry.has(sid):
                    errors.append({
                        "code": "CFG-003",
                        "field": f"audit.suites[{idx}].id",
                        "message": f"Configured suite is not registered: '{sid}'"
                    })
                    semantic_status = "FAIL"

                # CFG-007: required suite cannot be disabled
                is_req = s.get("required", False)
                is_enb = s.get("enabled", True)
                if is_req and not is_enb:
                    errors.append({
                        "code": "CFG-007",
                        "field": f"audit.suites[{idx}]",
                        "message": f"Contradiction: Required suite '{sid}' cannot be disabled (enabled: false)"
                    })
                    semantic_status = "FAIL"

                s_timeout = s.get("timeout_seconds")
                if s_timeout is not None and (not isinstance(s_timeout, (int, float)) or s_timeout <= 0):
                    errors.append({
                        "code": "CFG-004",
                        "field": f"audit.suites[{idx}].timeout_seconds",
                        "message": f"Suite '{sid}' timeout_seconds must be a positive number"
                    })
                    semantic_status = "FAIL"

        # Evidence checks
        evidence = audit.get("evidence", {})
        ev_enabled = evidence.get("enabled", True)
        # CFG-008: evidence must be enabled in strict mode
        if is_strict and not ev_enabled:
            errors.append({
                "code": "CFG-008",
                "field": "audit.evidence.enabled",
                "message": "Evidence collection cannot be disabled in strict execution mode"
            })
            semantic_status = "FAIL"

        # CFG-009: output dir check
        out_dir = evidence.get("output_dir")
        if out_dir:
            out_path = Path(out_dir)
            if ".." in out_path.parts:
                errors.append({
                    "code": "CFG-009",
                    "field": "audit.evidence.output_dir",
                    "message": "Evidence output directory must not contain path traversal (..)"
                })
                semantic_status = "FAIL"

        # Traceability checks
        traceability = audit.get("traceability", {})
        # CFG-010: traceability cannot be disabled in strict mode
        if is_strict and (not traceability.get("capture_commit", True) or not traceability.get("capture_environment", True)):
            errors.append({
                "code": "CFG-010",
                "field": "audit.traceability",
                "message": "Commit and environment traceability cannot be disabled in strict mode"
            })
            semantic_status = "FAIL"

        # 3. Operational Validation
        operational_status = "PASS"
        if semantic_status == "PASS" and schema_status == "PASS":
            # Check Python executable
            if not Path(sys.executable).is_file():
                errors.append({
                    "code": "CFG-OPER-001",
                    "field": "environment",
                    "message": f"Python executable '{sys.executable}' is not accessible"
                })
                operational_status = "FAIL"

        overall_status = "VALID" if (schema_status == "PASS" and semantic_status == "PASS" and operational_status == "PASS") else "INVALID"
        config_hash = compute_configuration_hash(config) if overall_status == "VALID" else ""

        return {
            "configuration_status": overall_status,
            "schema_validation": schema_status,
            "semantic_validation": semantic_status,
            "operational_validation": operational_status,
            "configuration_hash": config_hash,
            "errors": errors,
            "warnings": warnings
        }
