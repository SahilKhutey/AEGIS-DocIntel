#!/usr/bin/env python3
"""
scripts/check_dependency_sync.py
================================
pyproject.toml is the SINGLE SOURCE OF TRUTH for dependencies. The
``requirements-*.txt`` files are generated mirrors of it.

Why this exists: before this tool the repo had two hand-maintained dependency
lists that silently drifted apart (``hypothesis`` was declared in pyproject but
not in requirements-dev.txt; python-docx/pptx/openpyxl were declared nowhere;
version caps differed). CI installed from one list while the README told users
to install from another, so the documented install path aborted with zero tests
run while CI "looked" fine.

Usage:
    python scripts/check_dependency_sync.py            # check (exit 1 on drift)
    python scripts/check_dependency_sync.py --write    # regenerate the mirrors
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# requirements file -> (pyproject group, extra "-r" includes)
#   group "core" means [project].dependencies; anything else is an extra.
MIRRORS: dict[str, tuple[str, tuple[str, ...]]] = {
    "requirements-core.txt": ("core", ()),
    "requirements-ml.txt": ("ml", ("requirements-core.txt",)),
    "requirements-infra.txt": ("infra", ("requirements-core.txt",)),
    "requirements-ocr.txt": ("ocr", ("requirements-core.txt",)),
    "requirements-ui.txt": ("ui", ("requirements-core.txt",)),
    "requirements-dev.txt": ("dev", ("requirements-core.txt",)),
}

HEADERS = {
    "core": "Core runtime: API + ingestion (PDF/DOCX/PPTX/XLSX) + math/graph engines.\n"
            "# Does NOT include embeddings/vector search (see requirements-ml.txt).",
    "ml": "Optional ML tier: semantic embeddings + vector search.\n"
          "# WARNING: sentence-transformers pulls in torch (multi-GB download).",
    "infra": "Optional infrastructure: Redis caching + OpenTelemetry tracing.",
    "ocr": "Optional OCR tier (also needs the `tesseract` system binary).",
    "ui": "Optional UI tier: Streamlit interactive visualization dashboard.",
    "dev": "Development & testing (pytest, hypothesis, linters, security scanners).",
}

BANNER = (
    "# GENERATED from pyproject.toml — DO NOT EDIT BY HAND.\n"
    "# Regenerate with: python scripts/check_dependency_sync.py --write\n"
)


def load_groups() -> dict[str, list[str]]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    groups = {"core": list(data["project"]["dependencies"])}
    for name, reqs in data["project"].get("optional-dependencies", {}).items():
        if name == "all":  # meta-extra referencing the others
            continue
        groups[name] = list(reqs)
    return groups


def render(group: str, includes: tuple[str, ...], reqs: list[str]) -> str:
    out = [BANNER, f"# AEGIS-DocIntel — {HEADERS[group]}\n"]
    for inc in includes:
        out.append(f"-r {inc}\n")
    if includes:
        out.append("\n")
    out.extend(f"{r}\n" for r in reqs)
    return "".join(out)


def parse_requirements(path: Path) -> list[str]:
    reqs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split(" #")[0].strip()
        if not line or line.startswith(("#", "-")):
            continue
        reqs.append(line)
    return reqs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="regenerate requirements-*.txt from pyproject.toml")
    args = ap.parse_args()

    groups = load_groups()
    problems: list[str] = []

    for fname, (group, includes) in MIRRORS.items():
        path = ROOT / fname
        expected = groups[group]
        if args.write:
            path.write_text(render(group, includes, expected), encoding="utf-8")
            print(f"wrote {fname}  ({len(expected)} requirements, group '{group}')")
            continue
        if not path.exists():
            problems.append(f"{fname}: MISSING (expected group '{group}')")
            continue
        actual = parse_requirements(path)
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        if missing:
            problems.append(f"{fname}: declared in pyproject.toml but MISSING here: {missing}")
        if extra:
            problems.append(f"{fname}: present here but NOT in pyproject.toml: {extra}")

    if args.write:
        return 0
    if problems:
        print("DEPENDENCY DRIFT DETECTED — pyproject.toml is the source of truth:\n")
        for p in problems:
            print("  ✗", p)
        print("\nFix: edit pyproject.toml, then run: python scripts/check_dependency_sync.py --write")
        return 1
    print(f"OK — {len(MIRRORS)} requirements files match pyproject.toml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
