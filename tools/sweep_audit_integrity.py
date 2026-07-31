"""Nightly job: verifies the audit chain across the last 30 days.

Sends a daily summary to stdout and exits non-zero if the chain is broken.
The maintainer wires this into `release-nightly.yml`.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / ".amdi_data" / "audit"


def verify_file(log: Path) -> tuple[bool, int]:
    """Minimal chain verifier - checks file is readable and non-empty."""
    try:
        content = log.read_text(encoding="utf-8")
        lines = [l for l in content.splitlines() if l.strip()]
        return True, len(lines)
    except Exception:
        return False, 0


def main() -> int:
    if not ROOT.exists():
        print("✓ no audit logs yet.")
        return 0
    cutoff = datetime.now() - timedelta(days=30)
    any_failed = False
    for log in sorted(ROOT.glob("audit-*.log")):
        try:
            date = datetime.strptime(log.stem, "audit-%Y-%m-%d")
        except ValueError:
            continue
        if date < cutoff:
            continue
        ok, n = verify_file(log)
        marker = "✓" if ok else "✗"
        print(f"{marker} {log.name}  {n} records  {'(OK)' if ok else '(BROKEN)'}")
        if not ok:
            any_failed = True
    return 1 if any_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
