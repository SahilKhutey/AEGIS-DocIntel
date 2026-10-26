#!/usr/bin/env python3
"""
scripts/mvp_readiness.py — Run and record AEGIS-DocIntel MVP readiness checks.

Examples:
    python scripts/mvp_readiness.py
    python scripts/mvp_readiness.py --quick
    python scripts/mvp_readiness.py --output artifacts/mvp-readiness.json

Exit codes:
    0 = every selected check passed
    1 = at least one selected check failed
    2 = invalid invocation or missing repository prerequisites
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent

BASELINE_CHECKS: List[Tuple[str, List[str]]] = [
    ("dependency_sync", [sys.executable, "scripts/check_dependency_sync.py"]),
    ("documentation_claims", [sys.executable, "scripts/check_docs_claims.py"]),
    ("code_linting", [sys.executable, "-m", "ruff", "check", "src", "tests", "scripts", "dashboard"]),
    ("security_audit", [sys.executable, "-m", "bandit", "-r", "src", "dashboard", "scripts", "-ll"]),
]

SECURITY_AND_FUNCTIONAL_CHECKS: List[Tuple[str, List[str]]] = [
    ("runtime_configuration", [sys.executable, "-m", "pytest", "tests/test_runtime_configuration.py", "-q"]),
    ("production_auth", [sys.executable, "-m", "pytest", "tests/test_production_auth.py", "tests/test_auth_guard.py", "-q"]),
    ("multitenancy_isolation", [sys.executable, "-m", "pytest", "tests/test_multitenancy_isolation.py", "-q"]),
    ("persistence_and_deletion", [sys.executable, "-m", "pytest", "tests/test_persistence_and_audit.py", "tests/test_document_deletion.py", "-q"]),
    ("extraction_and_grounding", [sys.executable, "-m", "pytest", "tests/test_extraction_fidelity.py", "tests/test_retrieval_grounding.py", "-q"]),
    ("mvp_end_to_end_workflow", [sys.executable, "-m", "pytest", "tests/test_mvp_workflow_acceptance.py", "-q"]),
    ("standalone_docprep", [sys.executable, "-m", "pytest", "aegis-docprep/tests", "-q"]),
]

EVALUATION_CHECKS: List[Tuple[str, List[str]]] = [
    ("evaluation_quality_gates", [sys.executable, "evaluation/scripts/run_all.py", "--fail-under-gates"]),
]

FULL_SUITE_CHECKS: List[Tuple[str, List[str]]] = [
    ("full_test_suite_coverage", [sys.executable, "-m", "pytest", "tests/", "--cov=src", "--cov-fail-under=75", "-q"]),
]


def get_git_info() -> Dict[str, str]:
    """Retrieve current git branch and commit SHA."""
    info = {"branch": "unknown", "commit": "unknown", "clean": "unknown"}
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True
        ).strip()
        info["branch"] = branch or "HEAD detached"
    except Exception:
        pass

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        info["commit"] = commit
    except Exception:
        pass

    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True
        ).strip()
        info["clean"] = "true" if not status else "false"
    except Exception:
        pass

    return info


def run_check(name: str, cmd: List[str]) -> Dict[str, Any]:
    """Execute a single verification command and capture diagnostic output."""
    t0 = time.perf_counter()
    env = os.environ.copy()
    env["AEGIS_ENVIRONMENT"] = env.get("AEGIS_ENVIRONMENT", "development")
    env["LLM_PROVIDER"] = env.get("LLM_PROVIDER", "mock")

    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            timeout=900,
        )
        duration_s = round(time.perf_counter() - t0, 2)
        passed = proc.returncode == 0
        tail = proc.stdout.strip().splitlines()[-10:] if proc.stdout else []
        err_tail = proc.stderr.strip().splitlines()[-10:] if proc.stderr else []

        return {
            "name": name,
            "command": " ".join(cmd),
            "status": "PASSED" if passed else "FAILED",
            "exit_code": proc.returncode,
            "duration_seconds": duration_s,
            "output_tail": tail,
            "error_tail": err_tail,
        }
    except subprocess.TimeoutExpired:
        duration_s = round(time.perf_counter() - t0, 2)
        return {
            "name": name,
            "command": " ".join(cmd),
            "status": "TIMED_OUT",
            "exit_code": -1,
            "duration_seconds": duration_s,
            "output_tail": [],
            "error_tail": ["Process timed out after 900 seconds"],
        }
    except Exception as exc:
        duration_s = round(time.perf_counter() - t0, 2)
        return {
            "name": name,
            "command": " ".join(cmd),
            "status": "ERROR",
            "exit_code": -2,
            "duration_seconds": duration_s,
            "output_tail": [],
            "error_tail": [str(exc)],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run and record AEGIS-DocIntel MVP readiness checks.")
    parser.add_argument("--quick", action="store_true", help="Run fast core acceptance and evaluation checks (skip full 1200+ suite).")
    parser.add_argument("--output", default="artifacts/mvp-readiness.json", help="Path to write readiness JSON report.")
    parser.add_argument("--fail-fast", action="store_true", help="Stop execution immediately after the first failure.")
    args = parser.parse_args()

    git_info = get_git_info()
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    checks_to_run: List[Tuple[str, List[str]]] = []
    checks_to_run.extend(BASELINE_CHECKS)
    checks_to_run.extend(SECURITY_AND_FUNCTIONAL_CHECKS)
    checks_to_run.extend(EVALUATION_CHECKS)

    if not args.quick:
        checks_to_run.extend(FULL_SUITE_CHECKS)

    print("=" * 72)
    print("AEGIS-DocIntel — MVP Readiness Acceptance Runner")
    print(f"Timestamp: {timestamp_utc}")
    print(f"Branch:    {git_info['branch']} ({git_info['commit'][:8]})")
    print(f"Mode:      {'QUICK' if args.quick else 'FULL'}")
    print(f"Checks:    {len(checks_to_run)} scheduled")
    print("=" * 72)

    results: List[Dict[str, Any]] = []
    any_failed = False

    for idx, (name, cmd) in enumerate(checks_to_run, 1):
        print(f"[{idx:02d}/{len(checks_to_run):02d}] Running {name}...", end=" ", flush=True)
        res = run_check(name, cmd)
        results.append(res)

        status_str = res["status"]
        duration = res["duration_seconds"]
        print(f"{status_str} ({duration}s)")

        if res["status"] != "PASSED":
            any_failed = True
            if res["error_tail"]:
                for line in res["error_tail"][-3:]:
                    print(f"     [err] {line}")
            if args.fail_fast:
                print("\n[!] --fail-fast enabled: aborting remaining checks.")
                break

    overall_status = "PASSED" if not any_failed else "FAILED"
    total_time = round(sum(r["duration_seconds"] for r in results), 2)
    passed_count = sum(1 for r in results if r["status"] == "PASSED")

    report: Dict[str, Any] = {
        "report_version": "1.0.0",
        "timestamp_utc": timestamp_utc,
        "environment": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "git_branch": git_info["branch"],
            "git_commit": git_info["commit"],
            "git_clean": git_info["clean"],
        },
        "summary": {
            "mode": "quick" if args.quick else "full",
            "overall_status": overall_status,
            "total_checks": len(results),
            "passed_checks": passed_count,
            "failed_checks": len(results) - passed_count,
            "total_duration_seconds": total_time,
        },
        "checks": results,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("-" * 72)
    print(f"Readiness Result: {overall_status} ({passed_count}/{len(results)} passed in {total_time}s)")
    print(f"Report written to: {out_path}")
    print("=" * 72)

    return 0 if not any_failed else 1


if __name__ == "__main__":
    sys.exit(main())
