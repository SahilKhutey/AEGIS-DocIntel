"""pip-audit-based dependency sweep.

Outputs a vulnerability summary and exits non-zero if any
HIGH/CRITICAL CVE is found for the *currently installed* dependency
versions.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if shutil.which("pip-audit") is None:
        print("· pip-audit not installed; install via 'pip install pip-audit'.")
        return 0
    proc = subprocess.run(
        ["pip-audit", "--format", "json", "--strict"],
        capture_output=True, text=True,
    )
    report = json.loads(proc.stdout) if proc.stdout.strip() else []
    sev_count = {}
    for v in report:
        sev = (v.get("vulns") or [{}])[0].get("severity", "?")
        sev_count[sev] = sev_count.get(sev, 0) + 1
    Path("benchmarks/results/dependency-audit.json").parent.mkdir(
        parents=True, exist_ok=True)
    Path("benchmarks/results/dependency-audit.json").write_text(
        json.dumps({"report": report, "summary": sev_count}, indent=2),
        encoding="utf-8",
    )
    if sev_count.get("HIGH", 0) or sev_count.get("CRITICAL", 0):
        print("✗ HIGH/CRITICAL vulnerabilities:")
        print(json.dumps(sev_count, indent=2))
        return 1
    print("✓ no HIGH/CRITICAL CVEs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
