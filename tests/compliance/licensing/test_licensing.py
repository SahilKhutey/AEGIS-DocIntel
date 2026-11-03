"""
tests/compliance/licensing/test_licensing.py
============================================
LIC-001 through LIC-010 tests verifying license reconciliation,
dual-licensing architecture, dependency SBOM generation, and compliance status.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from aegis.compliance.licensing.scanner import (
    DependencyLicenseScanner,
    LicenseClassification,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_lic_001_root_license_dual_architecture():
    """LIC-001: Root LICENSE declares dual-licensing architecture."""
    lic_path = REPO_ROOT / "LICENSE"
    assert lic_path.exists()
    content = lic_path.read_text(encoding="utf-8")
    assert "Dual-Licensing Architecture" in content
    assert "aegis-docprep" in content
    assert "Apache License, Version 2.0" in content
    assert "AMDI-OS" in content


def test_lic_002_aegis_docprep_apache2_license():
    """LIC-002: aegis-docprep contains Apache-2.0 LICENSE."""
    docprep_lic = REPO_ROOT / "aegis-docprep" / "LICENSE"
    assert docprep_lic.exists()
    content = docprep_lic.read_text(encoding="utf-8")
    assert "Apache License" in content
    assert "Version 2.0" in content


def test_lic_003_scanner_permissive_classification():
    """LIC-003: Scanner classifies permissive licenses as APPROVED."""
    scanner = DependencyLicenseScanner(REPO_ROOT)
    for lic in ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC"]:
        name, cls_type, status = scanner.resolve_python_package_license("dummy-pkg")
        assert status == "APPROVED"


def test_lic_004_scanner_strong_copyleft_classification():
    """LIC-004: Scanner classifies strong copyleft as PROHIBITED."""
    cls_type, status = DependencyLicenseScanner.classify_license("GPL-3.0-only")
    assert cls_type == LicenseClassification.STRONG_COPYLEFT
    assert status == "PROHIBITED"


def test_lic_005_scanner_dual_license_pymupdf():
    """LIC-005: Scanner handles dual-licensed PyMuPDF as CONDITIONAL."""
    name, cls_type, status = DependencyLicenseScanner.resolve_python_package_license("pymupdf")
    assert cls_type == LicenseClassification.DUAL_LICENSED
    assert "CONDITIONAL" in status
    assert "Artifex Commercial" in name


def test_lic_006_scan_python_dependencies():
    """LIC-006: Scanner scans Python dependencies from requirements-core.lock.txt."""
    scanner = DependencyLicenseScanner(REPO_ROOT)
    py_deps = scanner.scan_python_dependencies()
    assert len(py_deps) >= 50
    assert any(d.package_name == "pydantic" for d in py_deps)
    assert any(d.package_name == "numpy" for d in py_deps)


def test_lic_007_scan_npm_dependencies():
    """LIC-007: Scanner scans frontend NPM dependencies from web/package.json."""
    scanner = DependencyLicenseScanner(REPO_ROOT)
    npm_deps = scanner.scan_npm_dependencies()
    assert len(npm_deps) >= 15
    assert any(d.package_name == "next" for d in npm_deps)
    assert any(d.package_name == "react" for d in npm_deps)


def test_lic_008_generate_sbom_artifacts():
    """LIC-008: generate_sbom writes all expected machine-readable SBOM artifacts."""
    scanner = DependencyLicenseScanner(REPO_ROOT)
    report = scanner.generate_sbom("artifacts/licence-audit")
    audit_dir = REPO_ROOT / "artifacts" / "licence-audit"

    assert (audit_dir / "python-licenses.json").exists()
    assert (audit_dir / "npm-licenses.json").exists()
    assert (audit_dir / "license-compliance-report.json").exists()
    assert (audit_dir / "LICENSE_ARCHITECTURE.md").exists()


def test_lic_009_compliance_report_status():
    """LIC-009: license-compliance-report.json indicates COMPLIANT status."""
    audit_dir = REPO_ROOT / "artifacts" / "licence-audit"
    with open(audit_dir / "license-compliance-report.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["compliance_status"] == "COMPLIANT"
    assert data["prohibited_packages_count"] == 0
    assert data["conditional_packages_count"] == 1


def test_lic_010_total_audited_count():
    """LIC-010: Total audited package count is >= 80 packages."""
    audit_dir = REPO_ROOT / "artifacts" / "licence-audit"
    with open(audit_dir / "license-compliance-report.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_dependencies_audited"] >= 80
