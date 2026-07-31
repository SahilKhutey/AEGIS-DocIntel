"""Drift sweeper.

Walks the repo and looks for every symbol in
`tools/deprecation_matrix.json` that still appears in non-migration code.

Exits non-zero if any forbidden symbol is present. The accompanying
test proves it actually flags known offenders.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = Path(__file__).parent / "deprecation_matrix.json"


def load_matrix() -> dict[str, str]:
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def scan(text: str, *, patterns: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Return [(pattern_id, snippet), ...] for every match."""
    out: list[tuple[str, str]] = []
    for pid, pat in patterns:
        for m in re.finditer(pat, text):
            line_start = text.rfind("\n", 0, m.start()) + 1
            line_end = text.find("\n", m.end())
            if line_end == -1:
                line_end = len(text)
            out.append((pid, text[line_start:line_end].strip()))
    return out


SKIP = {"node_modules", "build", "dist", ".venv", ".git",
        "site-packages", "tests/migration", ".migration_backup",
        "_archive", "release", "patches", "benchmarks"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="also fail on warning-tier deprecations")
    ap.add_argument("--json",   action="store_true",
                    help="emit JSON report instead of human output")
    args = ap.parse_args()

    matrix = load_matrix()
    patterns = []
    for key, spec in matrix.items():
        if not args.strict and spec.get("severity") == "warn":
            continue
        patterns.append((key, spec["regex"]))

    hits: dict[str, list[dict]] = {}
    for f in ROOT.rglob("*.py"):
        if any(part in SKIP for part in f.parts):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            continue
        for pid, snippet in scan(text, patterns=patterns):
            hits.setdefault(pid, []).append({
                "file": str(f.relative_to(ROOT)),
                "snippet": snippet[:160],
            })

    report = {
        "strict":   args.strict,
        "findings": hits,
        "totals":   {pid: len(v) for pid, v in hits.items()},
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        if not hits:
            print("✓ No drift detected.")
            return 0
        print("✗ Drift detected:")
        for pid, lst in hits.items():
            print(f"  [{pid}] {len(lst)} hit(s):")
            for h in lst[:5]:
                print(f"      {h['file']}: {h['snippet']}")
        print(f"\n{sum(len(v) for v in hits.values())} total occurrence(s).")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
