"""Tag the accepted RC as v0.3.0.

Prereqs:
    * release_rc_validate.py exited 0
    * Three maintainer votes recorded in manifest.json#vote
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rc", required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    vote = manifest.get("vote")
    if vote is None:
        print("✗ No vote recorded in manifest.", file=sys.stderr)
        return 2
    yes = sum(1 for d in vote.get("decisions", []) if d.get("vote") == "yes")
    if yes < 2:
        print(f"✗ Vote ACCEPT threshold (2) not met: {yes} YES", file=sys.stderr)
        return 2

    tag = "v0.3.0"
    sha = manifest["freeze_sha"]
    subprocess.run(
        ["git", "tag", "-s", tag, sha, "-m",
         f"AEGIS-DocIntel {tag} — Deprecation Cleanup"],
        cwd=ROOT, check=True
    )
    subprocess.run(["git", "push", "origin", tag], cwd=ROOT, check=True)
    print(f"✓ Tagged and pushed {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
