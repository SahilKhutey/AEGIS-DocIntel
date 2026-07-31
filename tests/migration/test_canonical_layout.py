"""Assert that the canonical package layout is in place."""

from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "src" / "amdi"


# Every required package subdirectory MUST exist.
EXPECTED_PKGS = [
    "api/routers", "core", "engines", "retrieval", "retrieval/methods",
    "retrieval/backends", "ingestion", "jobs", "compliance", "entity",
    "versioning", "export", "query", "math_concepts", "connectors",
    "services", "ael",
]


def test_canonical_package_root() -> None:
    assert PKG.is_dir(), f"missing canonical package root: {PKG}"


@pytest.mark.parametrize("rel", EXPECTED_PKGS)
def test_required_subpackage_exists(rel: str) -> None:
    assert (PKG / rel).is_dir(), f"missing subpackage: amdi/{rel}"


def test_legacy_bridge_present() -> None:
    assert (PKG / "legacy_bridge.py").exists()


def test_no_top_level_main_py() -> None:
    """Single canonical entrypoint: src/amdi/__main__.py"""
    for rel in ("src/main.py", "backend/main.py", "backend/src/main.py"):
        assert not (ROOT / rel).exists(), f"legacy entrypoint found: {rel}"


def test_no_legacy_top_level_dirs() -> None:
    for legacy in ("backend",):
        p = ROOT / legacy
        assert not p.exists(), f"legacy tree present: {p}"


def test_init_files_everywhere() -> None:
    """Every directory under amdi must have __init__.py."""
    missing = []
    for d in PKG.rglob("*"):
        if d.is_dir() and not (d / "__init__.py").exists():
            missing.append(str(d.relative_to(ROOT)))
    assert not missing, f"directories missing __init__.py: {missing}"
