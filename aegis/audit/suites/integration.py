"""
aegis/audit/suites/integration.py
=================================
Integration audit suite executing API and end-to-end integration workflows for WP-08:
- Frontend CI Quality Gates (WP-08.01)
- API Contract & Schema Compatibility (WP-08.02)
- Browser User Journeys & Playwright E2E (WP-08.03)
- Complete Document-to-Report Workflows (WP-08.04)
- Deployment Verification & Staging Smoke Tests (WP-08.05)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from aegis.audit.suites.base import BaseAuditSuite


class IntegrationAuditSuite(BaseAuditSuite):
    suite_id = "integration"
    suite_name = "System Integration and Release Readiness Audit Suite"
    suite_version = "2.0.0"
    description = (
        "Validates full cross-component integration: frontend quality gates, API contracts, "
        "browser user journeys, complete document-to-report workflows, and staging deployment readiness."
    )
    tags = ["integration", "frontend", "api", "e2e", "workflow", "deployment"]

    def validate(self, context: Any) -> None:
        """Verify presence of integration contracts and directories."""
        root = Path(getattr(context, "root_dir", Path.cwd()))
        contracts_dir = root / "contracts"
        artifacts_dir = root / "artifacts" / "integration"
        if not contracts_dir.exists():
            raise FileNotFoundError(f"Contracts directory missing at {contracts_dir}")
        if not artifacts_dir.exists():
            raise FileNotFoundError(f"Integration artifacts directory missing at {artifacts_dir}")

    def execute(self, context: Any) -> Dict[str, Any]:
        """Execute all 5 WP-08 integration audit gates."""
        root = Path(getattr(context, "root_dir", Path.cwd()))
        artifacts_dir = root / "artifacts" / "integration"
        findings: List[Dict[str, Any]] = []
        artifacts: List[Dict[str, Any]] = []
        passed = 0
        failed = 0

        # Gate 1: Frontend CI (WP-08.01)
        try:
            fe_report = artifacts_dir / "frontend_ci" / "FRONTEND_CI_TEST_REPORT.json"
            fe_build = artifacts_dir / "frontend_ci" / "FRONTEND_BUILD_REPORT.json"
            if not fe_report.exists() or not fe_build.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-INT-FE-001",
                    "title": "Frontend CI report missing",
                    "severity": "HIGH",
                    "description": f"fe_report: {fe_report.exists()}, fe_build: {fe_build.exists()}",
                })
            else:
                with open(fe_report, "r", encoding="utf-8") as f:
                    fe_data = json.load(f)
                pass_rate = fe_data.get("pass_rate", 0.0)
                failed_cnt = fe_data.get("failed_scenarios", 99)
                if pass_rate == 1.0 and failed_cnt == 0:
                    passed += 1
                    artifacts.append({
                        "name": "frontend_ci_test_report",
                        "path": str(fe_report.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-INT-FE-002",
                        "title": "Frontend CI quality gates failed",
                        "severity": "CRITICAL",
                        "description": f"Pass rate: {pass_rate}, Failed: {failed_cnt}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-INT-FE-003",
                "title": "Frontend CI evaluation exception",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Gate 2: API Contract & Schema Compatibility (WP-08.02)
        try:
            api_report = artifacts_dir / "api_contract" / "API_CONTRACT_TEST_REPORT.json"
            api_compat = artifacts_dir / "api_contract" / "API_COMPATIBILITY_REPORT.json"
            if not api_report.exists() or not api_compat.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-INT-API-001",
                    "title": "API contract reports missing",
                    "severity": "HIGH",
                    "description": f"api_report: {api_report.exists()}, api_compat: {api_compat.exists()}",
                })
            else:
                with open(api_report, "r", encoding="utf-8") as f:
                    api_data = json.load(f)
                with open(api_compat, "r", encoding="utf-8") as f:
                    compat_data = json.load(f)
                pass_rate = api_data.get("pass_rate", 0.0)
                failed_cnt = api_data.get("failed_scenarios", 99)
                compat_status = compat_data.get("status", "FAIL")

                if pass_rate == 1.0 and failed_cnt == 0 and compat_status == "PASS":
                    passed += 1
                    artifacts.append({
                        "name": "api_contract_test_report",
                        "path": str(api_report.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-INT-API-002",
                        "title": "API contract validation failed",
                        "severity": "CRITICAL",
                        "description": f"Pass rate: {pass_rate}, Failed: {failed_cnt}, Compatibility: {compat_status}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-INT-API-003",
                "title": "API contract evaluation exception",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Gate 3: Browser E2E User Journeys (WP-08.03)
        try:
            e2e_report = artifacts_dir / "browser_e2e" / "BROWSER_E2E_TEST_REPORT.json"
            if not e2e_report.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-INT-E2E-001",
                    "title": "Browser E2E report missing",
                    "severity": "HIGH",
                    "description": f"Missing {e2e_report}",
                })
            else:
                with open(e2e_report, "r", encoding="utf-8") as f:
                    e2e_data = json.load(f)
                pass_rate = e2e_data.get("pass_rate", 0.0)
                failed_cnt = e2e_data.get("failed_scenarios", 99)

                if pass_rate == 1.0 and failed_cnt == 0:
                    passed += 1
                    artifacts.append({
                        "name": "browser_e2e_test_report",
                        "path": str(e2e_report.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-INT-E2E-002",
                        "title": "Browser E2E scenarios failed",
                        "severity": "CRITICAL",
                        "description": f"Pass rate: {pass_rate}, Failed: {failed_cnt}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-INT-E2E-003",
                "title": "Browser E2E evaluation exception",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Gate 4: Document-to-Report Workflow (WP-08.04)
        try:
            wf_report = artifacts_dir / "workflows" / "DOCUMENT_TO_REPORT_TEST_REPORT.json"
            wf_perf = artifacts_dir / "workflows" / "DOCUMENT_TO_REPORT_PERFORMANCE.json"
            if not wf_report.exists() or not wf_perf.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-INT-WF-001",
                    "title": "Document-to-report workflow report missing",
                    "severity": "HIGH",
                    "description": f"wf_report: {wf_report.exists()}, wf_perf: {wf_perf.exists()}",
                })
            else:
                with open(wf_report, "r", encoding="utf-8") as f:
                    wf_data = json.load(f)
                with open(wf_perf, "r", encoding="utf-8") as f:
                    perf_data = json.load(f)
                pass_rate = wf_data.get("pass_rate", 0.0)
                failed_cnt = wf_data.get("failed_scenarios", 99)
                metrics = perf_data.get("metrics", {})
                leakage = metrics.get("workflow_failure_rate", 1.0)
                cit_prec = metrics.get("citation_precision", 0.0)

                if pass_rate == 1.0 and failed_cnt == 0 and leakage == 0.0 and cit_prec == 1.0:
                    passed += 1
                    artifacts.append({
                        "name": "document_to_report_test_report",
                        "path": str(wf_report.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-INT-WF-002",
                        "title": "Document-to-report workflow quality gates failed",
                        "severity": "CRITICAL",
                        "description": f"Pass rate: {pass_rate}, Failed: {failed_cnt}, Failure rate: {leakage}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-INT-WF-003",
                "title": "Document-to-report workflow evaluation exception",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Gate 5: Deployment Verification & Staging Smoke Tests (WP-08.05)
        try:
            dep_report = artifacts_dir / "deployment" / "DEPLOYMENT_VERIFICATION_REPORT.json"
            dep_smoke = artifacts_dir / "deployment" / "STAGING_SMOKE_TEST_REPORT.json"
            if not dep_report.exists() or not dep_smoke.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-INT-DEP-001",
                    "title": "Deployment verification reports missing",
                    "severity": "HIGH",
                    "description": f"dep_report: {dep_report.exists()}, dep_smoke: {dep_smoke.exists()}",
                })
            else:
                with open(dep_report, "r", encoding="utf-8") as f:
                    dep_data = json.load(f)
                with open(dep_smoke, "r", encoding="utf-8") as f:
                    smoke_data = json.load(f)
                status = dep_data.get("overall_status", "FAIL")
                smoke_status = smoke_data.get("status", "FAIL")
                sec = dep_data.get("container_security", {}).get("status", "FAIL")

                if status == "PASS" and smoke_status == "PASS" and sec == "PASS":
                    passed += 1
                    artifacts.append({
                        "name": "deployment_verification_report",
                        "path": str(dep_report.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-INT-DEP-002",
                        "title": "Deployment verification gates failed",
                        "severity": "CRITICAL",
                        "description": f"Status: {status}, Smoke: {smoke_status}, Security: {sec}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-INT-DEP-003",
                "title": "Deployment verification evaluation exception",
                "severity": "HIGH",
                "description": str(exc),
            })

        status_result = "PASSED" if failed == 0 else "FAILED"
        return {
            "status": status_result,
            "statistics": {
                "total": passed + failed,
                "passed": passed,
                "failed": failed,
                "skipped": 0,
                "errors": 0,
            },
            "findings": findings,
            "artifacts": artifacts,
        }
