#!/usr/bin/env python3
"""
scripts/validate_audit_artifacts.py
===================================
Validates generated AEGIS-DocIntel audit evidence artifacts, schemas,
and release gate determinations.

Usage:
    python scripts/validate_audit_artifacts.py
    python scripts/validate_audit_artifacts.py --dir audit/runs/<run_id>
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def find_target_dir(specified_dir: str | None) -> Path:
    """Determine which audit directory to validate."""
    if specified_dir:
        p = Path(specified_dir)
        if not p.is_absolute():
            p = ROOT / p
        return p

    # Default to latest run under audit/runs/ if any exist, else audit/
    runs_dir = ROOT / "audit" / "runs"
    if runs_dir.is_dir():
        runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], key=os.path.getmtime, reverse=True)
        if runs:
            return runs[0]

    return ROOT / "audit"


class ArtifactValidator:
    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.audit_root = ROOT / "audit"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed: int = 0

    def assert_file_exists(self, rel_path: str, min_bytes: int = 10, base_dir: Optional[Path] = None) -> bool:
        """Verify file presence and non-trivial content length."""
        root = base_dir or self.target_dir
        p = root / rel_path
        if not p.is_file():
            self.errors.append(f"Missing mandatory artifact: {rel_path} in {root}")
            return False
        size = p.stat().st_size
        if size < min_bytes:
            self.errors.append(f"Artifact {rel_path} is unexpectedly small ({size} bytes) in {root}")
            return False
        self.checks_passed += 1
        return True

    def assert_valid_json(
        self,
        rel_path: str,
        required_keys: List[str] | None = None,
        base_dir: Optional[Path] = None,
    ) -> Dict[str, Any] | None:
        """Verify file is valid JSON and contains required keys."""
        root = base_dir or self.target_dir
        if not self.assert_file_exists(rel_path, base_dir=root):
            return None
        p = root / rel_path
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            if required_keys:
                missing = [k for k in required_keys if k not in data]
                if missing:
                    self.errors.append(f"{rel_path} in {root} missing required JSON keys: {missing}")
                    return None
            self.checks_passed += 1
            return data
        except Exception as e:
            self.errors.append(f"{rel_path} in {root} is invalid JSON: {e}")
            return None

    def assert_valid_csv(
        self,
        rel_path: str,
        min_rows: int = 1,
        required_columns: List[str] | None = None,
        base_dir: Optional[Path] = None,
    ) -> bool:
        """Verify file is a valid CSV with headers and minimum rows."""
        root = base_dir or self.target_dir
        if not self.assert_file_exists(rel_path, base_dir=root):
            return False
        p = root / rel_path
        try:
            with open(p, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    self.errors.append(f"{rel_path} in {root} is empty or has no CSV header")
                    return False
                if required_columns:
                    missing = [c for c in required_columns if c not in header]
                    if missing:
                        self.errors.append(f"{rel_path} in {root} missing required CSV columns: {missing}")
                        return False
                rows = list(reader)
                if len(rows) < min_rows:
                    self.errors.append(f"{rel_path} in {root} has only {len(rows)} data rows (expected >= {min_rows})")
                    return False
            self.checks_passed += 1
            return True
        except Exception as e:
            self.errors.append(f"{rel_path} in {root} is malformed CSV: {e}")
            return False

    def validate(self) -> bool:
        """Execute comprehensive validation suite on audit directory."""
        print(f"Validating audit evidence directory: {self.target_dir}\n")

        # 1. Manifests & inventories
        self.assert_valid_json("audit-manifest.json", ["project", "release_candidate", "commit_sha", "overall_status"])
        self.assert_valid_json("release-candidate.json", ["project", "release_candidate", "git", "status"])
        self.assert_valid_json("benchmark_manifest.json", ["project", "quality_gates", "performance_targets"])

        self.assert_valid_csv("function_inventory.csv", min_rows=10, required_columns=["function_id", "module", "symbol", "result"])
        self.assert_valid_csv("test_matrix.csv", min_rows=20, required_columns=["test_id", "category", "status"])
        self.assert_valid_csv("findings_register.csv", min_rows=1, required_columns=["finding_id", "priority", "status"])

        # 2. Inventory directory
        self.assert_valid_csv("inventory/module-inventory.csv", min_rows=10, required_columns=["module_name", "description"])
        self.assert_valid_csv("inventory/api-route-inventory.csv", min_rows=20, required_columns=["route_id", "method", "path"])
        self.assert_valid_csv("inventory/feature-scope-matrix.csv", min_rows=10, required_columns=["feature_area", "mvp_scope"])

        # 3. Test specifications
        self.assert_valid_csv("test-specifications/unit-test-matrix.csv", min_rows=10)
        self.assert_valid_csv("test-specifications/integration-test-matrix.csv", min_rows=5)
        self.assert_valid_csv("test-specifications/security-test-matrix.csv", min_rows=5)
        self.assert_valid_csv("test-specifications/e2e-test-matrix.csv", min_rows=3)
        self.assert_valid_csv("test-specifications/acceptance-test-matrix.csv", min_rows=5)

        # 4. Benchmark results
        self.assert_valid_json("benchmarks/extraction-results.json")
        self.assert_valid_json("benchmarks/retrieval-results.json")
        self.assert_valid_json("benchmarks/intelligence-results.json")
        self.assert_valid_json("benchmarks/packing-results.json")
        self.assert_valid_json("benchmarks/performance-results.json")
        self.assert_valid_json("benchmarks/memory-results.json")

        # 5. Security & Reliability
        self.assert_valid_json("security/tenant-isolation-results.json")
        self.assert_valid_json("security/dependency-audit.json")
        self.assert_valid_json("security/bandit-report.json")
        self.assert_valid_json("security/secret-scan-summary.json")
        self.assert_valid_csv("security/security-findings.csv", min_rows=1)

        self.assert_valid_json("reliability/job-recovery-results.json")
        self.assert_valid_json("reliability/backup-restore-results.json")
        self.assert_valid_json("reliability/migration-results.json")
        self.assert_valid_json("reliability/failure-injection-results.json")

        # 6. Results & Reports
        self.assert_valid_json("results/coverage-summary.json")
        self.assert_valid_json("results/test-failures.json")
        self.assert_valid_json("results/regression-results.json")

        self.assert_file_exists("final/release-verification-report.md", min_bytes=500)
        self.assert_file_exists("final/release-decision.md", min_bytes=200)
        self.assert_file_exists("final/known-limitations.md", min_bytes=300)
        self.assert_valid_csv("final/risk-register.csv", min_rows=3)

        # 7. Check audit-manifest overall_status vs gate records
        manifest_path = self.target_dir / "audit-manifest.json"
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                records = manifest.get("gate_records", [])
                for r in records:
                    gid = r.get("gate_id", "UNKNOWN")
                    passed = r.get("passed", False)
                    if not passed and manifest.get("overall_status") == "PASS":
                        self.errors.append(f"Manifest inconsistency: gate {gid} failed but overall_status is PASS!")
            except Exception as e:
                self.errors.append(f"Failed verifying manifest gate records: {e}")

        # 8. Baseline & Audit Infrastructure (WP-01 & WP-02)
        print("Validating baseline and audit infrastructure specifications...")
        # 8a. Baseline (audit/baseline/)
        self.assert_valid_json("baseline/repository-manifest.json", ["project", "release_candidate", "git", "runtime", "lockfiles"], base_dir=self.audit_root)
        self.assert_valid_json("baseline/git-state.json", ["head_commit", "master_commit", "main_commit", "branches_aligned", "working_tree_clean"], base_dir=self.audit_root)
        self.assert_valid_json("baseline/dependency-inventory.json", ["python_runtime", "packages", "lockfiles"], base_dir=self.audit_root)
        self.assert_valid_json("baseline/environment.json", ["os_platform", "python_io_encoding", "system_environment_vars"], base_dir=self.audit_root)
        self.assert_valid_json("baseline/ci-baseline.json", ["ci_provider", "workflows"], base_dir=self.audit_root)
        self.assert_valid_csv("baseline/source-classification.csv", min_rows=15, required_columns=["path", "classification", "audit_treatment"], base_dir=self.audit_root)
        self.assert_valid_csv("baseline/capability-inventory.csv", min_rows=10, required_columns=["capability_id", "mvp_phase", "feature", "current_status"], base_dir=self.audit_root)

        # 8b. Config (audit/config/)
        self.assert_valid_json("config/audit_config.json", ["name", "profiles", "thresholds"], base_dir=self.audit_root)
        self.assert_valid_json("config/quality_gates.json", ["quality_gates"], base_dir=self.audit_root)
        self.assert_file_exists("config/capability_map.yaml", min_bytes=100, base_dir=self.audit_root)

        # 8c. Corpus (audit/corpus/)
        self.assert_valid_csv("corpus/manifest.csv", min_rows=200, required_columns=["doc_id", "category", "source_repository", "checksum_sha256"], base_dir=self.audit_root)
        self.assert_valid_csv("corpus/source-register.csv", min_rows=5, required_columns=["source_id", "source_name", "provider"], base_dir=self.audit_root)
        self.assert_valid_csv("corpus/licence-register.csv", min_rows=5, required_columns=["licence_id", "name", "spdx_identifier"], base_dir=self.audit_root)
        self.assert_file_exists("corpus/checksums.sha256", min_bytes=1000, base_dir=self.audit_root)

        # 8d. Specifications (audit/specifications/)
        self.assert_valid_csv("specifications/function-inventory.csv", min_rows=10, required_columns=["function_id", "module", "symbol", "result"], base_dir=self.audit_root)
        self.assert_valid_csv("specifications/test_matrix.csv", min_rows=20, required_columns=["test_id", "category", "status"], base_dir=self.audit_root)
        self.assert_valid_csv("specifications/acceptance-scenarios.csv", min_rows=5, required_columns=["scenario_id", "category", "status"], base_dir=self.audit_root)
        self.assert_file_exists("specifications/security-test-plan.md", min_bytes=500, base_dir=self.audit_root)

        # Summary output
        print("-" * 60)
        print(f"Validation Checks Passed: {self.checks_passed}")
        print(f"Validation Errors:        {len(self.errors)}")
        print(f"Validation Warnings:      {len(self.warnings)}")
        print("-" * 60)

        if self.errors:
            print("\nERRORS ENCOUNTERED:")
            for err in self.errors:
                print(f"  [!] {err}")
            return False

        print("\nAll audit evidence artifacts passed structural and schema validation.")
        return True


def main():
    parser = argparse.ArgumentParser(description="Validate AEGIS-DocIntel audit artifacts")
    parser.add_argument("--dir", help="Path to audit directory to validate")
    args = parser.parse_args()

    target_dir = find_target_dir(args.dir)
    validator = ArtifactValidator(target_dir)
    success = validator.validate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
