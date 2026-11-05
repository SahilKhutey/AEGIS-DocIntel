"""
aegis/audit/suites/security_reliability.py
==========================================
Audit suite executing Security & Reliability capability validations for WP-07:
Authentication (AUTH-001..012), Authorization & RBAC (RBAC-001..010),
Tenant Isolation (TENANT-001..012), Privacy & PII Leakage (PRIV-001..012),
Document Deletion & Tombstones (DEL-001..014), Worker Fault Tolerance (WORK-001..016),
and Clean Backup Restoration & Disaster Recovery (BACKUP-001..014).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import jsonschema

from aegis.audit.suites.base import BaseAuditSuite


class SecurityReliabilityAuditSuite(BaseAuditSuite):
    suite_id = "security_reliability"
    suite_name = "Security and Operational Reliability Audit Suite"
    suite_version = "1.0.0"
    description = (
        "Verifies authentication, authorization, tenant isolation, privacy detection, "
        "cascading document deletion, worker crash recovery, and disaster recovery backup restoration."
    )
    tags = [
        "security",
        "reliability",
        "authentication",
        "authorization",
        "tenant_isolation",
        "privacy",
        "deletion",
        "workers",
        "backup",
    ]

    def validate(self, context: Any) -> None:
        """Verify presence of security configurations and schemas."""
        root = Path(getattr(context, "root_dir", Path.cwd()))
        cfg_file = root / "configs" / "security" / "policy.yaml"
        schema_dir = root / "schemas" / "security"
        if not cfg_file.exists():
            raise FileNotFoundError(f"Security policy configuration missing at {cfg_file}")
        if not schema_dir.exists():
            raise FileNotFoundError(f"Security schema directory missing at {schema_dir}")

    def execute(self, context: Any) -> Dict[str, Any]:
        """Execute all WP-07 security & reliability audit checks."""
        root = Path(getattr(context, "root_dir", Path.cwd()))
        reports_dir = root / "artifacts" / "security" / "reports"
        schema_dir = root / "schemas" / "security"
        findings: List[Dict[str, Any]] = []
        artifacts: List[Dict[str, Any]] = []
        passed = 0
        failed = 0

        # Load benchmark and test schemas
        bench_schema = {}
        bench_schema_path = schema_dir / "benchmark.schema.json"
        if bench_schema_path.exists():
            with open(bench_schema_path, "r", encoding="utf-8") as f:
                bench_schema = json.load(f)

        # Check 1: Authentication Benchmark (AUTH-001 through AUTH-012)
        try:
            auth_path = reports_dir / "AUTHENTICATION_TEST_REPORT.json"
            if not auth_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-SEC-AUTH-001",
                    "title": "Authentication test report missing",
                    "severity": "HIGH",
                    "description": f"Missing {auth_path}",
                })
            else:
                with open(auth_path, "r", encoding="utf-8") as f:
                    auth_data = json.load(f)
                m = auth_data.get("metrics", {})
                pass_rate = m.get("authentication_pass_rate", 0.0)
                failed_cnt = m.get("failed_scenarios", 99)
                lockout = m.get("lockout_enforced", False)
                sig_ok = m.get("signature_verification_enforced", False)

                if pass_rate == 1.0 and failed_cnt == 0 and lockout and sig_ok:
                    passed += 1
                    artifacts.append({
                        "name": "authentication_test_report",
                        "path": str(auth_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-SEC-AUTH-002",
                        "title": "Authentication security gates failed",
                        "severity": "CRITICAL",
                        "description": f"Pass rate: {pass_rate}, Failed: {failed_cnt}, Lockout: {lockout}, Sig: {sig_ok}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-SEC-AUTH-003",
                "title": "Authentication audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 2: Authorization & RBAC Benchmark (RBAC-001 through RBAC-010)
        try:
            rbac_path = reports_dir / "AUTHORIZATION_TEST_REPORT.json"
            if not rbac_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-SEC-RBAC-001",
                    "title": "Authorization test report missing",
                    "severity": "HIGH",
                    "description": f"Missing {rbac_path}",
                })
            else:
                with open(rbac_path, "r", encoding="utf-8") as f:
                    rbac_data = json.load(f)
                m = rbac_data.get("metrics", {})
                pass_rate = m.get("authorization_pass_rate", 0.0)
                failed_cnt = m.get("failed_scenarios", 99)
                escalation_blocked = m.get("privilege_escalation_blocked", False)
                deny_default = m.get("deny_by_default_enforced", False)

                if pass_rate == 1.0 and failed_cnt == 0 and escalation_blocked and deny_default:
                    passed += 1
                    artifacts.append({
                        "name": "authorization_test_report",
                        "path": str(rbac_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-SEC-RBAC-002",
                        "title": "Authorization and privilege escalation gates failed",
                        "severity": "CRITICAL",
                        "description": f"Pass rate: {pass_rate}, Failed: {failed_cnt}, Escalation: {escalation_blocked}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-SEC-RBAC-003",
                "title": "Authorization audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 3: Tenant Isolation Benchmark (TENANT-001 through TENANT-012)
        try:
            ten_path = reports_dir / "TENANT_ISOLATION_TEST_REPORT.json"
            if not ten_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-SEC-TEN-001",
                    "title": "Tenant isolation test report missing",
                    "severity": "HIGH",
                    "description": f"Missing {ten_path}",
                })
            else:
                with open(ten_path, "r", encoding="utf-8") as f:
                    ten_data = json.load(f)
                m = ten_data.get("metrics", {})
                disclosures = m.get("cross_tenant_disclosures", 99)
                mutations = m.get("cross_tenant_modifications", 99)
                pass_rate = m.get("isolation_pass_rate", 0.0)

                if disclosures == 0 and mutations == 0 and pass_rate == 1.0:
                    passed += 1
                    artifacts.append({
                        "name": "tenant_isolation_test_report",
                        "path": str(ten_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-SEC-TEN-002",
                        "title": "Cross-tenant data disclosure or mutation detected",
                        "severity": "CRITICAL",
                        "description": f"Disclosures: {disclosures}, Modifications: {mutations}, Pass Rate: {pass_rate}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-SEC-TEN-003",
                "title": "Tenant isolation audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 4: Privacy & PII Detection Benchmark (PRIV-001 through PRIV-012)
        try:
            priv_path = reports_dir / "PRIVACY_DETECTION_REPORT.json"
            leak_path = reports_dir / "PRIVACY_OUTPUT_LEAKAGE_REPORT.json"
            if not priv_path.exists() or not leak_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-SEC-PRIV-001",
                    "title": "Privacy detection or leakage report missing",
                    "severity": "HIGH",
                    "description": f"priv_path: {priv_path.exists()}, leak_path: {leak_path.exists()}",
                })
            else:
                with open(priv_path, "r", encoding="utf-8") as f:
                    priv_data = json.load(f)
                with open(leak_path, "r", encoding="utf-8") as f:
                    leak_data = json.load(f)
                pm = priv_data.get("metrics", {})
                prec = pm.get("precision", 0.0)
                rec = pm.get("recall", 0.0)
                leak_rate = pm.get("output_leakage_rate", 1.0)
                sanitized = leak_data.get("telemetry_sanitization_verified", False)

                if prec >= 0.85 and rec >= 0.85 and leak_rate == 0.0 and sanitized:
                    passed += 1
                    artifacts.append({
                        "name": "privacy_detection_report",
                        "path": str(priv_path.relative_to(root).as_posix()),
                    })
                    artifacts.append({
                        "name": "privacy_output_leakage_report",
                        "path": str(leak_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-SEC-PRIV-002",
                        "title": "Privacy detection precision/recall or secret leakage gate violated",
                        "severity": "CRITICAL",
                        "description": f"Precision: {prec}, Recall: {rec}, Leakage Rate: {leak_rate}, Sanitized: {sanitized}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-SEC-PRIV-003",
                "title": "Privacy audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 5: Document Deletion & Tombstones (DEL-001 through DEL-014)
        try:
            del_path = reports_dir / "DOCUMENT_DELETION_TEST_REPORT.json"
            cmp_path = reports_dir / "DELETION_COMPLETENESS_REPORT.json"
            if not del_path.exists() or not cmp_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-SEC-DEL-001",
                    "title": "Document deletion or completeness report missing",
                    "severity": "HIGH",
                    "description": f"del_path: {del_path.exists()}, cmp_path: {cmp_path.exists()}",
                })
            else:
                with open(del_path, "r", encoding="utf-8") as f:
                    del_data = json.load(f)
                with open(cmp_path, "r", encoding="utf-8") as f:
                    cmp_data = json.load(f)
                dm = del_data.get("metrics", {})
                all_targets = dm.get("all_targets_verified", False)
                tombstone_ok = dm.get("tombstone_reconciliation_verified", False)
                pass_rate = dm.get("deletion_pass_rate", 0.0)
                residual = cmp_data.get("residual_data_detected", True)

                if all_targets and tombstone_ok and pass_rate == 1.0 and not residual:
                    passed += 1
                    artifacts.append({
                        "name": "document_deletion_test_report",
                        "path": str(del_path.relative_to(root).as_posix()),
                    })
                    artifacts.append({
                        "name": "deletion_completeness_report",
                        "path": str(cmp_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-SEC-DEL-002",
                        "title": "Document deletion completeness or tombstone reconciliation failed",
                        "severity": "CRITICAL",
                        "description": f"All Targets: {all_targets}, Tombstones: {tombstone_ok}, Residual Data: {residual}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-SEC-DEL-003",
                "title": "Document deletion audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 6: Background Worker Reliability (WORK-001 through WORK-016)
        try:
            work_path = reports_dir / "WORKER_RELIABILITY_REPORT.json"
            cst_path = reports_dir / "JOB_STATE_CONSISTENCY_REPORT.json"
            if not work_path.exists() or not cst_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-SEC-WRK-001",
                    "title": "Worker reliability or consistency report missing",
                    "severity": "HIGH",
                    "description": f"work_path: {work_path.exists()}, cst_path: {cst_path.exists()}",
                })
            else:
                with open(work_path, "r", encoding="utf-8") as f:
                    work_data = json.load(f)
                with open(cst_path, "r", encoding="utf-8") as f:
                    cst_data = json.load(f)
                wm = work_data.get("metrics", {})
                losses = wm.get("silent_job_losses", 99)
                dup_rate = wm.get("duplicate_execution_rate", 1.0)
                pass_rate = wm.get("worker_reliability_pass_rate", 0.0)
                orphans = cst_data.get("orphaned_jobs_count", 99)

                if losses == 0 and dup_rate == 0.0 and pass_rate == 1.0 and orphans == 0:
                    passed += 1
                    artifacts.append({
                        "name": "worker_reliability_report",
                        "path": str(work_path.relative_to(root).as_posix()),
                    })
                    artifacts.append({
                        "name": "job_state_consistency_report",
                        "path": str(cst_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-SEC-WRK-002",
                        "title": "Silent job loss or duplicate execution detected in worker subsystem",
                        "severity": "CRITICAL",
                        "description": f"Losses: {losses}, Dup Rate: {dup_rate}, Pass Rate: {pass_rate}, Orphans: {orphans}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-SEC-WRK-003",
                "title": "Worker reliability audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 7: Disaster Recovery & Backup Restoration (BACKUP-001 through BACKUP-014)
        try:
            rst_path = reports_dir / "RESTORATION_TEST_REPORT.json"
            itg_path = reports_dir / "BACKUP_INTEGRITY_REPORT.json"
            rpo_path = reports_dir / "RPO_RTO_MEASUREMENTS.json"
            if not rst_path.exists() or not itg_path.exists() or not rpo_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-SEC-DR-001",
                    "title": "Restoration, integrity, or RPO/RTO report missing",
                    "severity": "HIGH",
                    "description": f"rst_path: {rst_path.exists()}, itg_path: {itg_path.exists()}, rpo_path: {rpo_path.exists()}",
                })
            else:
                with open(rst_path, "r", encoding="utf-8") as f:
                    rst_data = json.load(f)
                with open(itg_path, "r", encoding="utf-8") as f:
                    itg_data = json.load(f)
                with open(rpo_path, "r", encoding="utf-8") as f:
                    rpo_data = json.load(f)
                rm = rst_data.get("metrics", {})
                db_ok = rm.get("database_integrity_verified", False)
                rto_ok = rm.get("rto_target_met", False)
                pass_rate = rm.get("restoration_pass_rate", 0.0)
                corrupt_rejected = itg_data.get("corrupted_backup_rejected", False)
                rpo_compliant = rpo_data.get("rpo_compliant", False)

                if db_ok and rto_ok and pass_rate == 1.0 and corrupt_rejected and rpo_compliant:
                    passed += 1
                    artifacts.append({
                        "name": "restoration_test_report",
                        "path": str(rst_path.relative_to(root).as_posix()),
                    })
                    artifacts.append({
                        "name": "backup_integrity_report",
                        "path": str(itg_path.relative_to(root).as_posix()),
                    })
                    artifacts.append({
                        "name": "rpo_rto_measurements",
                        "path": str(rpo_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-SEC-DR-002",
                        "title": "Disaster recovery restoration integrity or RTO/RPO target failed",
                        "severity": "CRITICAL",
                        "description": f"DB Verified: {db_ok}, RTO Met: {rto_ok}, Pass Rate: {pass_rate}, Corrupt Rejected: {corrupt_rejected}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-SEC-DR-003",
                "title": "Disaster recovery audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        status = "PASSED" if failed == 0 else "FAILED"
        return {
            "status": status,
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
