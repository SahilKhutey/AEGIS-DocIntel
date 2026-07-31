"""Remap tests to canonical layout + rebuild discovery roots.

After running, `pytest` is configured (in pyproject.toml) to discover:

    tests/

regardless of whether the original tests lived under:

    backend/tests/
    src/amdi/tests/
    tests/

Old roots are *moved* (not copied) so anyone running pytest immediately
sees the same set under the new path.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

CANONICAL_TEST_ROOT = Path("tests")


LEGACY_TEST_ROOTS = (
    Path("backend/tests"),
    Path("src/amdi/tests"),
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", type=Path)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    target = root / CANONICAL_TEST_ROOT
    target.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    for legacy in LEGACY_TEST_ROOTS:
        src = root / legacy
        if not src.exists():
            continue
        for f in src.rglob("*.py"):
            rel = f.relative_to(src)
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not args.apply:
                moved.append(f"DRY {f} → {dest}")
                continue
            shutil.move(str(f), str(dest))
            moved.append(f"MOVED {f} → {dest}")
        # remove empty legacy tree
        if args.apply and src.exists():
            shutil.rmtree(src, ignore_errors=True)

    for line in moved:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
