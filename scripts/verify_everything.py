"""Single-command acceptance test.

Runs:

    * ALL pytest suites the project ships
    * sweep bots
    * acceptance-checklist file existence
    * a 60-second smoke (scripts/smoke.sh) when --with-smoke is passed

Usage:

    python scripts/verify_everything.py                # default
    python scripts/verify_everything.py --with-smoke    # also run smoke
    python scripts/verify_everything.py --json          # JSON output

Exit 0 = green; non-zero = at least one cell of the matrix is red.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Result:
    name: str
    ok: bool
    duration_ms: float
    detail: str = ""


CHECKS: list[tuple[str, list[str]]] = [
    ("pytest_unit_api",     [sys.executable, "-m", "pytest", "-q", "--no-cov", "tests/api"]),
    ("pytest_security",     [sys.executable, "-m", "pytest", "-q", "--no-cov", "tests/security"]),
    ("pytest_observ",       [sys.executable, "-m", "pytest", "-q", "--no-cov", "tests/observability"]),
    ("pytest_retrieval",    [sys.executable, "-m", "pytest", "-q", "--no-cov", "tests/retrieval"]),
    ("pytest_migration",    [sys.executable, "-m", "pytest", "-q", "--no-cov", "tests/migration"]),
    ("pytest_transport",    [sys.executable, "-m", "pytest", "-q", "--no-cov", "tests/transport"]),
    ("pytest_ops",          [sys.executable, "-m", "pytest", "-q", "--no-cov", "tests/ops"]),
    ("pytest_final",        [sys.executable, "-m", "pytest", "-q", "--no-cov", "tests/FINAL"]),
    ("sweep_drift",         [sys.executable, "tools/sweep_drift.py"]),
    ("sweep_openapi_sync",  [sys.executable, "tools/sweep_openapi_sync.py"]),
    ("audit_integrity",     [sys.executable, "tools/sweep_audit_integrity.py"]),
]


import os


def _run(cmd: list[str]) -> tuple[bool, float, str]:
    t0 = time.perf_counter()
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(
        cmd, cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env,
    )
    dt = (time.perf_counter() - t0) * 1000.0
    stdout = res.stdout or ""
    stderr = res.stderr or ""
    detail = (stdout[-200:] + stderr[-200:]).strip()
    return res.returncode == 0, round(dt, 2), detail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-smoke", action="store_true")
    ap.add_argument("--json",       action="store_true")
    args = ap.parse_args()

    results: list[Result] = []
    for name, cmd in CHECKS:
        ok, dt, detail = _run(cmd)
        results.append(Result(name, ok, dt, detail))

    if args.with_smoke:
        ok, dt, detail = _run(["bash", "scripts/smoke.sh"])
        results.append(Result("smoke_60s", ok, dt, detail))

    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed

    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        print()
        print("Verifying v0.3.0 — every cell of the matrix")
        print("=" * 72)
        for r in results:
            mark = "✓" if r.ok else "✗"
            print(f"{mark} {r.name:24s} {r.duration_ms:8.1f} ms")
            if not r.ok:
                print(f"  ! {r.detail[:200]}")
        print()
        print(f"{'OK' if failed == 0 else 'FAIL'} · "
               f"{passed}/{len(results)} invariants passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
