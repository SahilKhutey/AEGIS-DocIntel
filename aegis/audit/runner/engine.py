"""
aegis/audit/runner/engine.py
============================
Central Audit Execution Engine coordinating the full audit lifecycle:
Configuration -> Traceability -> Planning -> Execution -> Evidence -> Provenance -> Reporting.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from aegis.audit.config.fingerprint import compute_configuration_hash
from aegis.audit.config.loader import AuditConfigLoader
from aegis.audit.config.validator import AuditConfigValidator
from aegis.audit.evidence.models import AuditRun
from aegis.audit.evidence.store import EvidenceStore
from aegis.audit.evidence.validator import EvidenceValidator
from aegis.audit.reporting.markdown import generate_markdown_summary
from aegis.audit.reporting.summary import compute_summary
from aegis.audit.runner.exceptions import (
    AuditError,
    ConfigurationError,
    ProvenanceError,
)
from aegis.audit.runner.executor import AuditExecutor
from aegis.audit.runner.planner import AuditPlanner, PlannedSuite
from aegis.audit.runner.registry import AuditRegistry
from aegis.audit.suites.corpus import CorpusAuditSuite
from aegis.audit.suites.intelligence import IntelligenceAuditSuite
from aegis.audit.suites.integration import IntegrationAuditSuite
from aegis.audit.suites.performance import PerformanceAuditSuite
from aegis.audit.suites.processing import ProcessingAuditSuite
from aegis.audit.suites.security import SecurityAuditSuite
from aegis.audit.suites.unit import UnitAuditSuite
from aegis.audit.traceability.environment_collector import EnvironmentCollector
from aegis.audit.traceability.git_collector import GitCollector
from aegis.audit.traceability.provenance_builder import ProvenanceBuilder
from aegis.audit.traceability.provenance_validator import ProvenanceValidator
from aegis.audit.traceability.run_identity import RunIdentity


class RunContext:
    """Carries runtime execution context, parameters, and error handlers."""

    def __init__(self, run_id: str, root_dir: Path) -> None:
        self.run_id = run_id
        self.root_dir = root_dir
        self.cleanup_errors: List[Dict[str, Any]] = []

    def record_cleanup_error(self, suite_id: str, exc: Exception) -> None:
        self.cleanup_errors.append({
            "suite_id": suite_id,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        })


class AuditRunner:
    """Authoritative Central Audit Runner."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str | Path] = None,
        registry: Optional[AuditRegistry] = None,
        evidence_store: Optional[EvidenceStore] = None,
        repo_path: Optional[str | Path] = None,
        trigger: str = "CLI",
    ) -> None:
        self.root_dir = Path(repo_path or ".").resolve()
        
        # 1. Registry initialization
        self.registry = registry or AuditRegistry()
        self._register_default_suites()

        # 2. Configuration loading
        if config is not None:
            self.config = config
        elif config_path:
            self.config = AuditConfigLoader.load(config_path)
        else:
            default_cfg_file = self.root_dir / "configs" / "audit" / "default.yaml"
            if default_cfg_file.is_file():
                self.config = AuditConfigLoader.load(default_cfg_file)
            else:
                self.config = {
                    "version": "1.0",
                    "audit": {
                        "name": "Default Fallback",
                        "enabled": True,
                        "execution": {"timeout_seconds": 600, "strict": False},
                        "suites": [{"id": "unit"}],
                        "evidence": {"enabled": True}
                    }
                }

        # 3. Evidence Store
        self.evidence_store = evidence_store or EvidenceStore(self.root_dir / "artifacts" / "audits")
        self.trigger = trigger

    def _register_default_suites(self) -> None:
        """Register built-in suites if not already present."""
        for suite_cls in [
            UnitAuditSuite,
            IntegrationAuditSuite,
            SecurityAuditSuite,
            PerformanceAuditSuite,
            CorpusAuditSuite,
            ProcessingAuditSuite,
            IntelligenceAuditSuite,
        ]:
            instance = suite_cls()
            if not self.registry.has(instance.suite_id):
                self.registry.register(instance)

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration contract."""
        return AuditConfigValidator.validate(
            self.config,
            registry=self.registry,
            base_dir=self.root_dir,
        )

    def run(
        self,
        suite_ids: Optional[List[str]] = None,
        all_suites: bool = False,
        dry_run: bool = False,
        profile_name: str = "default",
    ) -> Dict[str, Any]:
        # Step 1: Validate Configuration
        val_report = self.validate_configuration()
        if val_report["configuration_status"] != "VALID":
            err_msgs = [e["message"] for e in val_report.get("errors", [])]
            raise ConfigurationError(f"Audit configuration validation failed: {'; '.join(err_msgs)}")

        # Step 2: Build Plan
        plan = AuditPlanner.build_plan(
            self.config,
            self.registry,
            requested_suites=suite_ids,
            all_flag=all_suites,
        )

        if dry_run:
            return {
                "status": "DRY_RUN",
                "planned_suites_count": len(plan),
                "planned_suites": [s.suite_id for s in plan],
                "configuration_hash": val_report["configuration_hash"],
            }

        # Step 3: Capture Provenance & Run Context
        audit_cfg = self.config.get("audit", {})
        exec_cfg = audit_cfg.get("execution", {})
        is_strict = bool(exec_cfg.get("strict", False))
        fail_fast = bool(exec_cfg.get("fail_fast", False))

        run_id_info = RunIdentity.generate(
            prefix="AG",
            baseline_id="AEGIS-BASELINE-001",
            trigger=self.trigger,
        )
        run_id = run_id_info["run_id"]
        context = RunContext(run_id=run_id, root_dir=self.root_dir)

        git_collector = GitCollector(self.root_dir)
        git_snapshot = git_collector.collect()

        env_snapshot = EnvironmentCollector.collect(self.root_dir)
        cfg_snapshot = {
            "profile": profile_name,
            "sha256": val_report["configuration_hash"],
            "resolved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Step 4: Execute Suites
        executor = AuditExecutor(fail_fast=fail_fast)
        suite_results = executor.execute_plan(plan, context)
        completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Aggregate findings and artifacts
        all_findings = []
        all_artifacts = []
        for s in suite_results:
            all_findings.extend(s.get("findings", []))
            all_artifacts.extend(s.get("artifacts", []))

        # Determine overall status
        failed_count = sum(1 for s in suite_results if s.get("status") in {"FAILED", "ERROR", "TIMEOUT"})
        if failed_count == 0:
            overall_status = "PASSED"
        else:
            overall_status = "FAILED"

        # Step 5: Build Provenance Manifest
        provenance = ProvenanceBuilder.build(
            run_identity=run_id_info,
            git_snapshot=git_snapshot,
            config_snapshot=cfg_snapshot,
            env_snapshot=env_snapshot,
            started_at=started_at,
            completed_at=completed_at,
            artifact_count=len(all_artifacts),
        )

        # Enforce provenance rules (strict check)
        prov_errors = ProvenanceValidator.validate(provenance, strict_mode=is_strict)
        if prov_errors:
            overall_status = "BLOCKED"
            suite_results.append({
                "suite_id": "provenance_guard",
                "suite_version": "1.0.0",
                "status": "BLOCKED",
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_seconds": 0.0,
                "statistics": {"total": 1, "passed": 0, "failed": 1, "skipped": 0, "errors": 0},
                "findings": [{"finding_id": "FIND-PROV-001", "title": "Provenance failure", "severity": "CRITICAL", "description": "; ".join(prov_errors)}],
                "artifacts": []
            })

        # Step 6: Construct AuditRun Entity
        audit_run = AuditRun(
            run_id=run_id,
            baseline_id=run_id_info["baseline_id"],
            project="AEGIS-DocIntel",
            execution={
                "status": overall_status,
                "started_at": started_at,
                "completed_at": completed_at,
                "trigger": self.trigger,
            },
            source={
                "branch": git_snapshot["branch"],
                "commit_sha": git_snapshot["commit_sha"],
                "working_tree": "CLEAN" if git_snapshot["working_tree_clean"] else "MODIFIED",
            },
            configuration=cfg_snapshot,
            environment=env_snapshot,
            suites=suite_results,
            findings=all_findings,
            artifacts=all_artifacts,
        )

        # Step 7: Compute Summary and Markdown
        summary = compute_summary(audit_run.to_dict(), planned_count=len(plan))
        markdown_report = generate_markdown_summary(audit_run.to_dict(), summary)

        # Step 8: Persist Evidence
        run_dir = self.evidence_store.save_run(
            run=audit_run,
            summary=summary,
            summary_md=markdown_report,
            provenance_dict=provenance,
        )

        return {
            "run_id": run_id,
            "status": overall_status,
            "run_dir": str(run_dir),
            "summary": summary.to_dict(),
            "markdown": markdown_report,
        }
