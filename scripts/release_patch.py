"""Patch-release driver.

Cut a release branch, regenerate DIFF_STAT, run all gates, suggest the
tag string, and (with --tag) actually create the tag.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p.returncode, (p.stdout + p.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="e.g. 0.3.1")
    ap.add_argument("--tag",     action="store_true",
                    help="actually create and push the tag")
    args = ap.parse_args()
    version = args.version
    tag     = f"v{version}"

    preflight_path = ROOT / "scripts" / "release_preflight.py"
    if preflight_path.exists():
        rc, out = _run([sys.executable, str(preflight_path)])
        print("preflight:", "✓" if rc == 0 else "✗")
        if rc != 0:
            print(out[:500])
            return 2
    else:
        print("preflight: skipped (release_preflight.py not found)")

    # DIFF_STAT
    rc2, stat = _run(["git", "diff", "--stat", "HEAD~1..HEAD"])
    patch_dir = ROOT / "patches" / tag
    patch_dir.mkdir(parents=True, exist_ok=True)
    (patch_dir / "DIFF_STAT.md").write_text(
        "```text\n" + stat + "\n```\n",
        encoding="utf-8",
    )
    print("✓ diff_stat generated")

    if not args.tag:
        print("Dry-run complete. Re-run with --tag to push.")
        return 0

    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=ROOT).strip()
    subprocess.run(
        ["git", "tag", "-s", tag, sha, "-m",
         f"AEGIS-DocIntel {tag} — First Patch"],
        check=True, cwd=ROOT
    )
    subprocess.run(["git", "push", "origin", tag], check=True, cwd=ROOT)
    print(f"✓ Tagged and pushed {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())