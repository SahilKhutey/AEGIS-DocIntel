"""Pre-tag validation of the v0.3.0 RC.

Combines the canonical pre-flight + post-flight from Deliverable J with
the sweep bots from Deliverable K.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


STEPS: list[list[str]] = [
    [sys.executable, "scripts/release_preflight.py"],
    [sys.executable, "tools/sweep_drift.py", "--strict"],
    [sys.executable, "tools/sweep_openapi_sync.py"],
    [sys.executable, "tools/sweep_dependency_audit.py"],
    ["pytest", "tests/release", "tests/demo",
      "tests/migration", "tests/security", "tests/observability",
      "tests/api", "tests/export", "tests/retrieval", "tests/ops", "-q",
      "--ignore=tests/migration/test_legacy_bridge_removal_readiness.py"],
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rc", required=True)
    args = ap.parse_args()
    failed = 0
    print(f"Validating v0.3.0-rc.{args.rc}\n")
    for cmd in STEPS:
        try:
            res = subprocess.run(cmd, cwd=ROOT)
        except Exception as exc:  # noqa: BLE001
            print(f"✗ {cmd[1]} — {exc}")
            failed += 1
            continue
        marker = "✓" if res.returncode == 0 else "✗"
        print(f"{marker} {' '.join(cmd[1:])}")
        if res.returncode != 0:
            failed += 1
    print(f"\n{len(STEPS) - failed}/{len(STEPS)} gates passed.")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
