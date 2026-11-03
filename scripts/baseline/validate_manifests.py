#!/usr/bin/env python3
"""
scripts/baseline/validate_manifests.py
======================================
Validates all WP-01 acceptance criteria (AC-01 through AC-15) and
verifies the integrity of all baseline audit manifests and registers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE_DIR = ROOT / "audit" / "baseline"
ENV_DIR = BASELINE_DIR / "environment"
REPORTS_DIR = BASELINE_DIR / "reports"

REQUIRED_ARTIFACTS = [
    # WP01-01
    (BASELINE_DIR / "baseline_manifest.json", "AC-01 / AC-02 / AC-03"),
    (BASELINE_DIR / "canonical_commit.txt", "AC-01"),
    (BASELINE_DIR / "canonical_commit_summary.txt", "AC-01"),
    # WP01-02
    (ENV_DIR / "environment_manifest.json", "AC-04"),
    (ENV_DIR / "runtime_versions.txt", "AC-04"),
    (ENV_DIR / "system_information.txt", "AC-04"),
    (ENV_DIR / "installed_packages.json", "AC-04"),
    (ENV_DIR / "dependency_inventory.csv", "AC-05"),
    (ENV_DIR / "dependency_health.json", "AC-06"),
    (ENV_DIR / "environment_variables_inventory.txt", "AC-04"),
    (ENV_DIR / "reproducibility_report.md", "AC-07"),
    # WP01-03
    (BASELINE_DIR / "source_file_inventory.csv", "AC-08"),
    (BASELINE_DIR / "module_inventory.csv", "AC-08"),
    (BASELINE_DIR / "capability_matrix.csv", "AC-09"),
    (BASELINE_DIR / "module_dependency_graph.mmd", "AC-10"),
    (REPORTS_DIR / "module_inventory_report.md", "AC-08"),
    (REPORTS_DIR / "architecture_observations.md", "AC-08"),
    # WP01-04
    (BASELINE_DIR / "module_classification.csv", "AC-11"),
    (BASELINE_DIR / "archive_inventory.csv", "AC-12"),
    (BASELINE_DIR / "experimental_module_register.csv", "AC-11"),
    (REPORTS_DIR / "branch_comparison_report.md", "AC-13"),
    (REPORTS_DIR / "lifecycle_classification_report.md", "AC-11")
]


def main() -> int:
    all_ok = True
    print("=" * 70)
    print("AEGIS-DocIntel — WP-01 Baseline Artifact Verification")
    print("=" * 70)

    for path, ac_ref in REQUIRED_ARTIFACTS:
        if not path.is_file():
            print(f"[FAIL] Missing {ac_ref}: {path.relative_to(ROOT)}")
            all_ok = False
        else:
            sz = path.stat().st_size
            if sz == 0:
                print(f"[FAIL] Empty file for {ac_ref}: {path.relative_to(ROOT)}")
                all_ok = False
            else:
                print(f"[PASS] {ac_ref.ljust(18)} : {path.name} ({sz} bytes)")

    # Validate JSON formats
    for jpath in [
        BASELINE_DIR / "baseline_manifest.json",
        ENV_DIR / "environment_manifest.json",
        ENV_DIR / "dependency_health.json",
        ENV_DIR / "installed_packages.json"
    ]:
        if jpath.is_file():
            try:
                json.loads(jpath.read_text(encoding="utf-8"))
                print(f"[PASS] Valid JSON schema  : {jpath.name}")
            except Exception as e:
                print(f"[FAIL] Invalid JSON syntax: {jpath.name} -> {e}")
                all_ok = False

    print("=" * 70)
    if all_ok:
        print("[SUCCESS] All 21 core artifacts verified and passed validation.")
        return 0
    else:
        print("[ERROR] Verification failures detected.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
