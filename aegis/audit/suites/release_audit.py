"""
aegis/audit/suites/release_audit.py
===================================
Release audit suite executing final verification and release authorization for WP-09:
- Release Candidate Freeze (WP-09.01)
- Complete Verification (WP-09.02)
- Findings & Risk Assessment (WP-09.03)
- Evidence Package Integrity (WP-09.04)
- Independent Review Sign-off (WP-09.05)
- Release Authorization Decision (WP-09.06)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from aegis.audit.suites.base import BaseAuditSuite


class ReleaseAuditSuite(BaseAuditSuite):
    suite_id = "release_audit"
    suite_name = "Release Audit and Authorization Suite"
    suite_version = "1.0.0"
    description = (
        "Validates immutable release candidate freeze, full verification matrix, "
        "findings closure, evidence package, independent sign-off, and release decision."
    )
    tags = ["release", "audit", "wp09"]

    def validate(self, context: Any = None) -> None:
        """Verify presence of release candidate manifests and directories."""
        root = Path(getattr(context, "root_dir", Path.cwd()))
        manifest = root / "RELEASE_CANDIDATE_MANIFEST.json"
        if not manifest.exists():
            raise FileNotFoundError(f"Release candidate manifest missing: {manifest}")

    def execute(self, context: Any = None) -> Dict[str, Any]:
        root = Path(getattr(context, "root_dir", Path.cwd()))
        findings: List[Dict[str, Any]] = []
        artifacts: List[Dict[str, Any]] = []
        passed = 0
        failed = 0

        # Check 1: WP-09.01 Freeze Manifest
        m_path = root / "RELEASE_CANDIDATE_MANIFEST.json"
        if m_path.exists():
            with open(m_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("status") == "FROZEN" and len(data.get("git", {}).get("commit_sha", "")) == 40:
                passed += 1
                artifacts.append({"name": "RELEASE_CANDIDATE_MANIFEST.json", "status": "VALID"})
            else:
                failed += 1
                findings.append({"id": "FIND-REL-01", "severity": "HIGH", "message": "Invalid freeze manifest"})
        else:
            failed += 1
            findings.append({"id": "FIND-REL-01", "severity": "HIGH", "message": "Manifest missing"})

        # Check 2: WP-09.02 Full Verification Matrix
        v_path = root / "COMPLETE_VERIFICATION_REPORT.json"
        if v_path.exists():
            with open(v_path, "r", encoding="utf-8") as f:
                v_data = json.load(f)
            if v_data.get("verification_status") == "COMPLETED" and v_data.get("summary", {}).get("failed", 1) == 0:
                passed += 1
                artifacts.append({"name": "COMPLETE_VERIFICATION_REPORT.json", "status": "VALID"})
            else:
                failed += 1
                findings.append({"id": "FIND-REL-02", "severity": "HIGH", "message": "Verification failures present"})
        else:
            failed += 1
            findings.append({"id": "FIND-REL-02", "severity": "HIGH", "message": "Verification report missing"})

        # Check 3: WP-09.03 Zero Open Critical Findings
        f_path = root / "FINDINGS_CLOSURE_REPORT.json"
        if f_path.exists():
            with open(f_path, "r", encoding="utf-8") as f:
                f_data = json.load(f)
            if f_data.get("critical_blockers_remaining", 1) == 0 and f_data.get("release_gate_verdict") == "PASS":
                passed += 1
                artifacts.append({"name": "FINDINGS_CLOSURE_REPORT.json", "status": "VALID"})
            else:
                failed += 1
                findings.append({"id": "FIND-REL-03", "severity": "CRITICAL", "message": "Unresolved blockers"})
        else:
            failed += 1
            findings.append({"id": "FIND-REL-03", "severity": "CRITICAL", "message": "Findings report missing"})

        # Check 4: WP-09.04 Evidence Package Integrity
        e_path = root / "EVIDENCE_PACKAGE_VALIDATION_REPORT.json"
        if e_path.exists():
            with open(e_path, "r", encoding="utf-8") as f:
                e_data = json.load(f)
            if e_data.get("validation_verdict") == "PASS" and e_data.get("failed_checks", 1) == 0:
                passed += 1
                artifacts.append({"name": "EVIDENCE_PACKAGE_VALIDATION_REPORT.json", "status": "VALID"})
            else:
                failed += 1
                findings.append({"id": "FIND-REL-04", "severity": "HIGH", "message": "Evidence validation failure"})
        else:
            failed += 1
            findings.append({"id": "FIND-REL-04", "severity": "HIGH", "message": "Evidence validation report missing"})

        # Check 5: WP-09.05 Independent Sign-off
        s_path = root / "REVIEWER_SIGNOFF.md"
        if s_path.exists():
            content = s_path.read_text(encoding="utf-8")
            if "[x] **APPROVED**" in content:
                passed += 1
                artifacts.append({"name": "REVIEWER_SIGNOFF.md", "status": "APPROVED"})
            else:
                failed += 1
                findings.append({"id": "FIND-REL-05", "severity": "CRITICAL", "message": "Missing reviewer approval"})
        else:
            failed += 1
            findings.append({"id": "FIND-REL-05", "severity": "CRITICAL", "message": "Reviewer signoff missing"})

        # Check 6: WP-09.06 Release Decision (GO)
        d_path = root / "RELEASE_DECISION.json"
        if d_path.exists():
            with open(d_path, "r", encoding="utf-8") as f:
                d_data = json.load(f)
            if d_data.get("decision") == "GO" and d_data.get("open_blockers", 1) == 0:
                passed += 1
                artifacts.append({"name": "RELEASE_DECISION.json", "status": "GO"})
            else:
                failed += 1
                findings.append({"id": "FIND-REL-06", "severity": "CRITICAL", "message": "Decision not GO"})
        else:
            failed += 1
            findings.append({"id": "FIND-REL-06", "severity": "CRITICAL", "message": "Release decision missing"})

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
