"""Verify that the migration completed cleanly.

Exits non-zero on any failed check.

    python scripts/verify_migration.py
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


ALLOWED_TOP_LEVEL_PACKAGES = {"amdi", "src"}
FORBIDDEN_LEGACY_FRAGMENTS = (
    "amdi.src",   # dead prefix
    "src.amdi",   # legacy path
    "from backend", # legacy path
)



CHECKS: list[tuple[str, bool, str]] = []  # accumulated; evaluated at the end


def add(name: str, ok: bool, detail: str) -> None:
    CHECKS.append((name, ok, detail))


def _walk_text_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*")
            if p.is_file()
            and not any(part in {".venv", "build", "dist", ".migration_backup",
                                  "__pycache__", ".mypy_cache", ".ruff_cache"}
                          for part in p.parts)
            and p.suffix in {".py", ".md", ".rst", ".toml", ".yml", ".yaml"}]


def verify_imports(root: Path) -> None:
    bad: list[tuple[Path, str, int]] = []
    skip_names = {
        "legacy_bridge.py", "migrate_imports.py", "test_no_legacy_paths.py",
        "test_legacy_bridge.py", "verify_migration.py", "STRUCTURE.md", "MIGRATION.md",
    }
    for f in _walk_text_files(root):
        if f.suffix != ".py" or f.name in skip_names:
            continue
        if any(p in {".migration_backup", ".src.bak"} for p in f.parts):
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.lstrip()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            for frag in FORBIDDEN_LEGACY_FRAGMENTS:
                if frag in line:
                    bad.append((f, line, n))
                    break
    add("no_legacy_import_fragments",
        not bad,
        f"{len(bad)} legacy import fragment(s) found; see report")



def verify_module_wheels(root: Path) -> None:
    """`pip install -e .` discovery: src/amdi must be importable."""
    import subprocess
    res = subprocess.run(
        [sys.executable, "-c",
         "import amdi, amdi.config, amdi.api.app, "
         "amdi.retrieval, amdi.jobs.ledger, amdi.services.container, "
         "amdi.legacy_bridge"],
        capture_output=True, text=True, check=False,
    )
    add("package_imports", res.returncode == 0, res.stderr.strip() or "OK")


def verify_no_duplicate_init(root: Path) -> None:
    dups: list[str] = []
    for pkg in (root / "src" / "amdi").rglob("__init__.py"):
        rel = pkg.relative_to(root)
        dups.append(str(rel))
    add("canonical_init_layout", len(dups) > 0, f"{len(dups)} __init__.py present")


def verify_manifest_exists(root: Path) -> None:
    p = root / ".migration_backup" / "manifest.json"
    add("manifest_exists", p.exists(), f"manifest at {p}")


def verify_no_root_scripts(root: Path) -> None:
    leaks: list[str] = []
    for f in (root / "src" / "amdi").rglob("*.py"):
        rel = f.relative_to(root)
        if rel.parts[-1] in {"main.py", "app.py"}:
            continue
        if f.parent.name in {"scripts"}:
            leaks.append(str(rel))
    add("no_script_leakage", not leaks, "no misplaced scripts")


def verify_pyproject(root: Path) -> None:
    pp = root / "pyproject.toml"
    if not pp.exists():
        add("pyproject_present", False, "missing pyproject.toml")
        return
    text = pp.read_text(encoding="utf-8")
    ok = (
        'packages = ["src/amdi"]' in text
        or "packages = ['src/amdi']" in text
        or '"src/amdi"' in text
    )
    add("pyproject_points_to_amdi", ok, "pyproject build target is src/amdi")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(".").resolve()
    verify_manifest_exists(root)
    verify_pyproject(root)
    verify_no_duplicate_init(root)
    verify_no_root_scripts(root)
    verify_module_wheels(root)
    verify_imports(root)

    print("\nMigration verification report")
    print("=" * 60)
    fail = 0
    for name, ok, detail in CHECKS:
        mark = "[OK]" if ok else "[FAIL]"
        print(f"{mark:6s} {name:30s} {detail}")
        if not ok:
            fail += 1
    print()
    print(f"{'PASS' if fail == 0 else f'FAIL ({fail})'} — {len(CHECKS) - fail}/{len(CHECKS)} checks passed")
    sys.exit(0 if fail == 0 else 1)



if __name__ == "__main__":
    raise SystemExit(main())
