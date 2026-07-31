"""RC-specific manifest generator.

Builds on `release_manifest.py` (Deliverable J); adds:

  * RC number
  * freeze SHA
  * candidate-acceptance votes
  * sweep-bot results (drift, openapi, audit, deps)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p.returncode, (p.stdout + p.stderr).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rc", required=True, help="e.g. 1, 2, 3")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    rc2, sha = _run(["git", "rev-parse", "HEAD"])
    rc_tag = f"v0.3.0-rc.{args.rc}"

    sweeps = {}
    for sweep, label in [
        ([str(ROOT / "tools" / "sweep_drift.py"), "--strict"], "drift"),
        ([str(ROOT / "tools" / "sweep_openapi_sync.py")],      "openapi_sync"),
        ([str(ROOT / "tools" / "sweep_audit_integrity.py")],   "audit_integrity"),
        ([str(ROOT / "tools" / "sweep_dependency_audit.py")],  "deps_cve"),
    ]:
        rc, out = _run([sys.executable] + sweep)
        sweeps[label] = {"exit": rc, "summary": out[:200]}

    payload = {
        "candidate": rc_tag,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "freeze_sha": sha.strip(),
        "sweeps": sweeps,
        "vote": None,
        "links": {
            "charter":   "release/v0.3.0-rc/CHARTER.md",
            "checklist": "release/v0.3.0-rc/CHECKLIST.md",
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if all(v["exit"] == 0 for v in sweeps.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
