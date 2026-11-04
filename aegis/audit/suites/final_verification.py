"""
aegis/audit/suites/final_verification.py
========================================
Authoritative Final System Verification and Certification Suite for WP-FINAL:
- WP-FINAL.01: Repository & Architecture Audit
- WP-FINAL.02: Requirements Traceability
- WP-FINAL.03: Complete Functional Testing
- WP-FINAL.04: Unit & Component Testing
- WP-FINAL.05: Integration & System Testing
- WP-FINAL.06: Document Processing Validation
- WP-FINAL.07: Intelligence & Grounding Validation
- WP-FINAL.08: Security & Privacy Validation
- WP-FINAL.09: Reliability & Recovery Testing
- WP-FINAL.10: Performance & Benchmarking
- WP-FINAL.11: Documentation & Evidence Consolidation
- WP-FINAL.12: Final System Validation & Certification
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from aegis.audit.suites.base import BaseAuditSuite


class FinalVerificationSuite(BaseAuditSuite):
    suite_id = "final_verification"
    suite_name = "Final System Verification and Certification Suite (WP-FINAL)"
    suite_version = "1.0.0"
    description = (
        "Consolidates and validates all 12 engineering verification packages in "
        "release/final-verification/, documentation completeness in docs/, and formal certification."
    )
    tags = ["final", "verification", "certification", "wp_final"]

    def validate(self, context: Any = None) -> None:
        root = Path(getattr(context, "root_dir", Path.cwd()))
        target_dir = root / "release" / "final-verification"
        if not target_dir.exists():
            raise FileNotFoundError(f"Final verification directory missing: {target_dir}")

    def execute(self, context: Any = None) -> Dict[str, Any]:
        root = Path(getattr(context, "root_dir", Path.cwd()))
        base = root / "release" / "final-verification"
        findings: List[Dict[str, Any]] = []
        artifacts: List[Dict[str, Any]] = []
        passed = 0
        failed = 0

        # Sub-Package 1: Repository & Architecture Audit
        d01 = base / "01_repository_audit"
        m_inv = d01 / "MODULE_IMPLEMENTATION_INVENTORY.csv"
        dep_g = d01 / "DEPENDENCY_GRAPH.json"
        if m_inv.exists() and dep_g.exists():
            passed += 1
            artifacts.append({"sub_package": "WP-FINAL.01", "status": "VERIFIED"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-01", "severity": "HIGH", "message": "WP-FINAL.01 audit assets missing"})

        # Sub-Package 2: Requirements Traceability
        d02 = base / "02_requirements"
        req_cov = d02 / "REQUIREMENT_COVERAGE_REPORT.json"
        if req_cov.exists():
            with open(req_cov, "r", encoding="utf-8") as f:
                rdata = json.load(f)
            if rdata.get("coverage_percentage", 0.0) == 100.0 and rdata.get("unverified_requirements", 1) == 0:
                passed += 1
                artifacts.append({"sub_package": "WP-FINAL.02", "status": "VERIFIED"})
            else:
                failed += 1
                findings.append({"id": "FIND-FIN-02", "severity": "HIGH", "message": "Unverified requirements remain"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-02", "severity": "HIGH", "message": "Requirement coverage report missing"})

        # Sub-Package 3: Complete Functional Testing
        d03 = base / "03_functional"
        f_res = d03 / "FUNCTIONAL_TEST_RESULTS.json"
        if f_res.exists():
            with open(f_res, "r", encoding="utf-8") as f:
                fdata = json.load(f)
            if fdata.get("status") == "ALL_PASSED" and fdata.get("failed", 1) == 0:
                passed += 1
                artifacts.append({"sub_package": "WP-FINAL.03", "status": "VERIFIED"})
            else:
                failed += 1
                findings.append({"id": "FIND-FIN-03", "severity": "HIGH", "message": "Functional test failures detected"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-03", "severity": "HIGH", "message": "Functional test results missing"})

        # Sub-Package 4: Unit & Component Testing
        d04 = base / "04_unit_component"
        u_res = d04 / "UNIT_TEST_RESULTS.json"
        cov_res = d04 / "CODE_COVERAGE_REPORT.json"
        if u_res.exists() and cov_res.exists():
            with open(u_res, "r", encoding="utf-8") as f:
                udata = json.load(f)
            with open(cov_res, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            if udata.get("failed", 1) == 0 and cdata.get("statement_coverage_percentage", 0) > 90.0:
                passed += 1
                artifacts.append({"sub_package": "WP-FINAL.04", "status": "VERIFIED"})
            else:
                failed += 1
                findings.append({"id": "FIND-FIN-04", "severity": "HIGH", "message": "Unit/Coverage gate failure"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-04", "severity": "HIGH", "message": "Unit test report missing"})

        # Sub-Package 5: Integration & System Testing
        d05 = base / "05_integration_system"
        sys_res = d05 / "SYSTEM_TEST_REPORT.json"
        if sys_res.exists():
            with open(sys_res, "r", encoding="utf-8") as f:
                sdata = json.load(f)
            if sdata.get("pass_rate", 0) == 100.0:
                passed += 1
                artifacts.append({"sub_package": "WP-FINAL.05", "status": "VERIFIED"})
            else:
                failed += 1
                findings.append({"id": "FIND-FIN-05", "severity": "HIGH", "message": "System test failures present"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-05", "severity": "HIGH", "message": "System test report missing"})

        # Sub-Package 6: Document Processing Validation
        d06 = base / "06_processing"
        ocr_rep = d06 / "OCR_BENCHMARK_REPORT.json"
        tab_rep = d06 / "TABLE_RECONSTRUCTION_REPORT.json"
        if ocr_rep.exists() and tab_rep.exists():
            with open(ocr_rep, "r", encoding="utf-8") as f:
                ocr_d = json.load(f)
            with open(tab_rep, "r", encoding="utf-8") as f:
                tab_d = json.load(f)
            if ocr_d.get("character_error_rate", 1.0) < 0.02 and tab_d.get("teds_score", 0.0) > 0.90:
                passed += 1
                artifacts.append({"sub_package": "WP-FINAL.06", "status": "VERIFIED"})
            else:
                failed += 1
                findings.append({"id": "FIND-FIN-06", "severity": "HIGH", "message": "Processing accuracy below threshold"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-06", "severity": "HIGH", "message": "Processing benchmark reports missing"})

        # Sub-Package 7: Intelligence Validation
        d07 = base / "07_intelligence"
        cit_rep = d07 / "CITATION_CORRECTNESS_REPORT.json"
        abs_rep = d07 / "ABSTENTION_REPORT.json"
        if cit_rep.exists() and abs_rep.exists():
            with open(cit_rep, "r", encoding="utf-8") as f:
                cit_d = json.load(f)
            with open(abs_rep, "r", encoding="utf-8") as f:
                abs_d = json.load(f)
            if cit_d.get("unsupported_claims", 1) == 0 and abs_d.get("abstention_precision", 0.0) > 0.95:
                passed += 1
                artifacts.append({"sub_package": "WP-FINAL.07", "status": "VERIFIED"})
            else:
                failed += 1
                findings.append({"id": "FIND-FIN-07", "severity": "CRITICAL", "message": "Unsupported claims or hallucination detected"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-07", "severity": "HIGH", "message": "Intelligence validation reports missing"})

        # Sub-Package 8: Security & Privacy Validation
        d08 = base / "08_security_privacy"
        ten_rep = d08 / "TENANT_ISOLATION_REPORT.json"
        priv_rep = d08 / "PRIVACY_VALIDATION_REPORT.json"
        if ten_rep.exists() and priv_rep.exists():
            with open(ten_rep, "r", encoding="utf-8") as f:
                ten_d = json.load(f)
            with open(priv_rep, "r", encoding="utf-8") as f:
                priv_d = json.load(f)
            if not ten_d.get("cross_tenant_leakage_detected", True) and priv_d.get("telemetry_leakage", 1.0) == 0.0:
                passed += 1
                artifacts.append({"sub_package": "WP-FINAL.08", "status": "VERIFIED"})
            else:
                failed += 1
                findings.append({"id": "FIND-FIN-08", "severity": "CRITICAL", "message": "Security or tenant isolation violation"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-08", "severity": "HIGH", "message": "Security reports missing"})

        # Sub-Package 9: Reliability & Recovery Testing
        d09 = base / "09_reliability_recovery"
        bak_rep = d09 / "BACKUP_RESTORATION_REPORT.json"
        wrk_rep = d09 / "WORKER_FAULT_INJECTION_REPORT.json"
        if bak_rep.exists() and wrk_rep.exists():
            with open(bak_rep, "r", encoding="utf-8") as f:
                bak_d = json.load(f)
            with open(wrk_rep, "r", encoding="utf-8") as f:
                wrk_d = json.load(f)
            if bak_d.get("restoration_success_rate", 0.0) == 1.0 and wrk_d.get("recovery_success_rate", 0.0) == 1.0:
                passed += 1
                artifacts.append({"sub_package": "WP-FINAL.09", "status": "VERIFIED"})
            else:
                failed += 1
                findings.append({"id": "FIND-FIN-09", "severity": "HIGH", "message": "Recovery or restoration failure"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-09", "severity": "HIGH", "message": "Reliability reports missing"})

        # Sub-Package 10: Performance & Benchmarking
        d10 = base / "10_benchmarks"
        api_perf = d10 / "API_PERFORMANCE_REPORT.json"
        if api_perf.exists():
            with open(api_perf, "r", encoding="utf-8") as f:
                api_d = json.load(f)
            if api_d.get("latency_p95_ms", 1000.0) < 100.0:
                passed += 1
                artifacts.append({"sub_package": "WP-FINAL.10", "status": "VERIFIED"})
            else:
                failed += 1
                findings.append({"id": "FIND-FIN-10", "severity": "MEDIUM", "message": "API latency exceeded SLA"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-10", "severity": "HIGH", "message": "API performance report missing"})

        # Sub-Package 11: Documentation Completeness
        d11 = base / "11_documentation"
        doc_audit = d11 / "DOCUMENTATION_COMPLETENESS_AUDIT.csv"
        if doc_audit.exists():
            passed += 1
            artifacts.append({"sub_package": "WP-FINAL.11", "status": "VERIFIED"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-11", "severity": "HIGH", "message": "Documentation audit missing"})

        # Sub-Package 12: Final Certification & Sign-off
        d12 = base / "12_final_assessment"
        f_ver = d12 / "FINAL_VERIFICATION_REPORT.json"
        manifest = d12 / "FINAL_EVIDENCE_MANIFEST.json"
        signoff = d12 / "WP_FINAL_SIGNOFF.md"
        if f_ver.exists() and manifest.exists() and signoff.exists():
            with open(f_ver, "r", encoding="utf-8") as f:
                f_d = json.load(f)
            if f_d.get("verdict") == "CERTIFIED_READY_FOR_RELEASE":
                passed += 1
                artifacts.append({"sub_package": "WP-FINAL.12", "status": "VERIFIED"})
            else:
                failed += 1
                findings.append({"id": "FIND-FIN-12", "severity": "CRITICAL", "message": "Final certification rejected"})
        else:
            failed += 1
            findings.append({"id": "FIND-FIN-12", "severity": "HIGH", "message": "Final assessment assets missing"})

        status = "PASSED" if failed == 0 else "FAILED"
        return {
            "status": status,
            "statistics": {
                "total": 12,
                "passed": passed,
                "failed": failed,
                "skipped": 0,
                "errors": 0,
            },
            "findings": findings,
            "artifacts": artifacts,
        }
