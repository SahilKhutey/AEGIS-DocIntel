#!/usr/bin/env python3
"""
scripts/run_mvp_acceptance.py
=============================
Phase 3.5 Production Readiness & Release Qualification:
Unified acceptance and release qualification test runner.
Executes all pre-flight integrity checks, security test suites, integration & recovery suites,
and evaluation quality benchmark gates. Emits a structured qualification report.

Usage:
    python scripts/run_mvp_acceptance.py [--quick] [--output artifacts/phase3/mvp-release-report.json]

Exit codes:
    0 = All qualification gates passed (Release: GO)
    1 = One or more qualification gates failed (Release: NO-GO)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent

# Step definitions: (id, name, command_list)
PREFLIGHT_GATES: List[Tuple[str, str, List[str]]] = [
    ("dependency_sync", "Dependency Synchronization", [sys.executable, "scripts/check_dependency_sync.py"]),
    ("docs_claims", "Documentation Claims Verification", [sys.executable, "scripts/check_docs_claims.py"]),
    ("dataset_contract", "MVP Dataset Contract & Integrity", [sys.executable, "scripts/validate_mvp_dataset.py"]),
    ("release_config", "Release Configuration Validation", [sys.executable, "scripts/validate_release_config.py", "--env", "development"]),
]

SECURITY_GATES: List[Tuple[str, str, List[str]]] = [
    ("security_acceptance", "Security Acceptance Suite (Auth, Roles, Tenant Isolation)", [sys.executable, "-m", "pytest", "tests/security/", "-q"]),
]

WORKFLOW_GATES: List[Tuple[str, str, List[str]]] = [
    ("integration_acceptance", "Integration & Recovery Suite (Workflow, Persistence, Backup, Recovery)", [sys.executable, "-m", "pytest", "tests/integration/", "-q"]),
]

EVALUATION_GATES: List[Tuple[str, str, List[str]]] = [
    ("evaluation_acceptance", "Evaluation Test Suite (Citations, Context Budget)", [sys.executable, "-m", "pytest", "tests/evaluation/", "-q"]),
    ("quality_benchmarks", "Quality Benchmark Gates (Extraction, Retrieval, Packing, Redaction)", [
        sys.executable, "evaluation/scripts/run_all.py", "--fail-under-gates",
        "--output", "artifacts/phase3/evaluation-report.json"
    ]),
]


def get_git_metadata() -> Dict[str, str]:
    """Capture current git branch, commit hash, and status."""
    meta = {"branch": "unknown", "commit": "unknown", "clean": "unknown"}
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        meta["branch"] = branch
        meta["commit"] = commit
        meta["clean"] = "true" if not status else "false"
    except Exception:
        pass
    return meta


def run_gate(gate_id: str, gate_name: str, cmd: List[str]) -> Dict[str, Any]:
    """Execute a single qualification gate command and capture stdout/stderr and timing."""
    start_time = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300,
        )
        duration = round(time.time() - start_time, 2)
        passed = (proc.returncode == 0)
        output = proc.stdout.strip()
    except subprocess.TimeoutExpired:
        duration = round(time.time() - start_time, 2)
        passed = False
        output = "Gate timed out after 300 seconds."
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        passed = False
        output = f"Execution error: {e}"

    return {
        "gate_id": gate_id,
        "name": gate_name,
        "command": " ".join(cmd),
        "passed": passed,
        "duration_seconds": duration,
        "summary": output.splitlines()[-1] if output else "",
        "output": output,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="AEGIS-DocIntel MVP Acceptance and Release Qualification")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "phase3" / "mvp-release-report.json",
                        help="Path to write the release report JSON")
    parser.add_argument("--quick", action="store_true", help="Skip expensive quality benchmarks")
    args = parser.parse_args()

    start_all = time.time()
    git_meta = get_git_metadata()

    gates_to_run = list(PREFLIGHT_GATES) + list(SECURITY_GATES) + list(WORKFLOW_GATES)
    if args.quick:
        gates_to_run += [list(EVALUATION_GATES)[0]]
    else:
        gates_to_run += list(EVALUATION_GATES)

    print("=" * 75)
    print(" AEGIS-DocIntel — Phase 3 Release Qualification Runner")
    print(f" Git Commit : {git_meta['commit'][:10]} ({git_meta['branch']})")
    print(f" Timestamp  : {datetime.now(timezone.utc).isoformat()}")
    print("=" * 75)

    gate_results: List[Dict[str, Any]] = []
    overall_passed = True

    for gate_id, gate_name, cmd in gates_to_run:
        print(f"\n>> Executing Gate: {gate_name}...")
        res = run_gate(gate_id, gate_name, cmd)
        gate_results.append(res)
        status_tag = "[PASS]" if res["passed"] else "[FAIL]"
        print(f"   {status_tag} {res['name']} ({res['duration_seconds']}s)")
        if not res["passed"]:
            overall_passed = False
            print(f"   Error summary: {res['summary']}")

    total_duration = round(time.time() - start_all, 2)
    decision = "GO" if overall_passed else "NO-GO"

    print("\n" + "=" * 75)
    print(f" RELEASE QUALIFICATION DECISION: {decision}")
    print(f" Gates Passed : {sum(1 for r in gate_results if r['passed'])}/{len(gate_results)}")
    print(f" Total Time   : {total_duration}s")
    print("=" * 75)

    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git": git_meta,
        "decision": decision,
        "overall_passed": overall_passed,
        "total_duration_seconds": total_duration,
        "gates_count": len(gate_results),
        "gates_passed": sum(1 for r in gate_results if r["passed"]),
        "gates": [
            {
                "gate_id": r["gate_id"],
                "name": r["name"],
                "passed": r["passed"],
                "duration_seconds": r["duration_seconds"],
                "command": r["command"],
                "summary": r["summary"],
            }
            for r in gate_results
        ],
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        print(f"\nStructured qualification report saved to: {args.output}")

    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
