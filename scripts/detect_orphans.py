"""Find Python files that nothing else imports.

Heuristic:
1. Walk all .py files
2. Collect their 'import X' / 'from X import Y' statements
3. Mark X.Y as 'used'
4. Anything in src/amdi/ not in 'used' that isn't an __init__.py is a candidate orphan

Print a JSON report. Does not delete anything — review before removing.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

EXCLUDE_DIRS = {".venv", "build", "dist", ".mypy_cache",
                ".ruff_cache", ".pytest_cache", "__pycache__",
                ".migration_backup"}

EXCLUDE_TOP_LEVEL = {
    # Common stdlib / 3rd-party top-levels we don't want to "use"
    "__future__", "abc", "asyncio", "collections", "dataclasses", "datetime",
    "enum", "functools", "hashlib", "itertools", "json", "logging", "math",
    "os", "pathlib", "re", "sys", "time", "typing", "uuid",
    "numpy", "scipy", "networkx", "sklearn", "sympy",
    "pymupdf", "pdfplumber", "PIL", "librosa", "soundfile",
    "pytesseract", "pdf2image", "fastapi", "uvicorn", "pydantic",
    "httpx", "tenacity", "PyJWT", "cryptography",
    "sentence_transformers", "rank_bm25", "structlog",
    "arq", "datasets", "ragas", "deepeval", "faiss",
    "pytest", "tests", "benchmarks", "scripts",
    "matplotlib", "pandas",
    "importlib",  # common dynamic import
}

ROOT_PKG = "amdi"


def _is_local_module(mod: str) -> bool:
    return mod == ROOT_PKG or mod.startswith(ROOT_PKG + ".")


def _scan_imports(py_file: Path, repo_root: Path) -> set[str]:
    """Return the set of *local* module names that this file imports."""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    used: set[str] = set()
    for node in ast.walk(tree):
        target = _import_target(node)
        if target and _is_local_module(target.split(".")[0]):
            used.add(target)
    return used


def _import_target(node) -> str | None:
    if isinstance(node, ast.Import):
        return node.names[0].name
    if isinstance(node, ast.ImportFrom):
        if node.module is None:
            return None
        if node.level and node.level > 0:
            # relative imports; won't process for orphan detection — they
            # only mean something within the same package anyway.
            return None
        return node.module
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", type=Path)
    args = ap.parse_args(argv)
    root = args.root.resolve()

    files = [p for p in root.rglob("*.py")
             if not any(part in EXCLUDE_DIRS for part in p.parts)]
    module_to_files: dict[str, list[Path]] = {}
    file_to_uses: dict[Path, set[str]] = {}

    for f in files:
        if f.name == "__init__.py":
            continue
        mod = _module_name_for(f, root)
        if mod:
            module_to_files.setdefault(mod, []).append(f)
        file_to_uses[f] = _scan_imports(f, root)

    # A module is "used" if it appears in ANY file_to_uses.
    used_modules: set[str] = set()
    for uses in file_to_uses.values():
        used_modules.update(uses)

    orphans = []
    for f in files:
        if f.name == "__init__.py":
            continue
        mod = _module_name_for(f, root)
        if mod and mod not in used_modules:
            orphans.append(str(f.relative_to(root)))

    print(json.dumps({
        "scanned_files": len(files),
        "used_modules": sorted(used_modules),
        "orphan_files": sorted(orphans),
    }, indent=2))
    return 0


def _module_name_for(f: Path, root: Path) -> str | None:
    rel = f.relative_to(root)
    parts = list(rel.parts)
    if "src" not in parts:
        return None
    idx = parts.index("src")
    after = parts[idx + 1:]
    after[-1] = after[-1][:-3]  # strip .py
    if after[-1] == "__init__":
        after.pop()
    return ".".join(after)


if __name__ == "__main__":
    raise SystemExit(main())
