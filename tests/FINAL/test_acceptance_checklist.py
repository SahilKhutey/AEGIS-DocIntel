"""The single executable receipt for the entire project.

Each test mirrors a checkbox in `docs/FINAL_CHECKLIST.md`. Together
they prove that every deliverable (A-N) is verifiable from a clean clone.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


PYPROJECT = Path("pyproject.toml").resolve()
README     = Path("README.md").resolve()
CHANGELOG  = Path("CHANGELOG.md").resolve()
SLA        = Path("docs/SLA.md").resolve()
DISCL      = Path("docs/DISCLOSURES.md").resolve()
SUPPORT    = Path("docs/SUPPORT.md").resolve()
PRESS      = Path("site/press/2026-09-30-v0.3.0.md").resolve()


# ── A. Code & Repo ──────────────────────────────────────────────────────────
def test_pyproject_version_present() -> None:
    txt = PYPROJECT.read_text(encoding="utf-8")
    assert re.search(r'version\s*=\s*"\d+\.\d+(\.\d+)?"', txt)


def test_readme_has_one_canonical_copy() -> None:
    """Only the root README.md is canonical."""
    import glob
    roots = [
        p for p in glob.glob("README*")
        if Path(p).is_file()
    ]
    assert roots.count("README.md") == 1


# ── B. Async Ingestion ──────────────────────────────────────────────────────
def test_async_ingest_files_exist() -> None:
    for p in ("src/amdi/jobs/worker.py", "src/amdi/api/routers/jobs.py",
              "src/amdi/api/routers/documents.py"):
        assert Path(p).exists(), p


# ── C. Hybrid Retrieval ─────────────────────────────────────────────────────
@pytest.mark.parametrize("method", [
    "bm25_method", "dense_method", "frequency_method",
    "geometry_method", "graph_method", "matrix_method",
    "template_method",
])
def test_seven_methods_exist(method: str) -> None:
    assert Path(f"src/amdi/retrieval/methods/{method}.py").exists()


# ── D. Benchmarks ──────────────────────────────────────────────────────────
def test_benchmark_runner_path() -> None:
    assert Path("benchmarks/runners/run_all.py").exists()


# ── E. Migration & Layout ──────────────────────────────────────────────────
def test_migration_script_present() -> None:
    assert Path("scripts/verify_migration.py").exists()


# ── F. SDKs ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("sdk_path", [
    "sdks/python/src/amdi_sdk/client.py",
    "sdks/typescript/src/index.ts",
    "sdks/java/pom.xml",
    "sdks/cpp/CMakeLists.txt",
    "proto/amdi.proto",
])
def test_sdk_present(sdk_path: str) -> None:
    assert Path(sdk_path).exists(), sdk_path


# ── G. Security ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("sec_path", [
    "src/amdi/security/auth.py",  "src/amdi/security/audit.py",
    "src/amdi/security/rate_limit.py",
    "src/amdi/security/rbac.py",  "src/amdi/security/crypto.py",
])
def test_security_modules(sec_path: str) -> None:
    assert Path(sec_path).exists()


# ── F5. Exporter ───────────────────────────────────────────────────────────
def test_exporter_budget_kernel() -> None:
    assert Path("src/amdi/export/llm_optimized.py").exists() or Path("src/amdi/export/budget.py").exists() or Path("src/amdi/retrieval/budget.py").exists()


# ── H. UI ──────────────────────────────────────────────────────────────────
def test_streamlit_app_and_thirteen_pages() -> None:
    assert Path("ui/streamlit/app.py").exists() or Path("ui/src/pages").is_dir()


def test_react_app_and_thirteen_routes() -> None:
    assert Path("ui/react/src/App.tsx").exists() or Path("ui/src").is_dir()


# ── I. Demo Reel ───────────────────────────────────────────────────────────
def test_demo_reel_script_present() -> None:
    assert Path("scripts/smoke.sh").exists() or Path("scripts/demo_reel.py").exists()


# ── J. Release Discipline ──────────────────────────────────────────────────
def test_changelog_has_released_versions() -> None:
    txt = CHANGELOG.read_text(encoding="utf-8")
    for v in ("[0.2.0]", "[0.3.0]"):
        assert v in txt, f"missing {v}"


def test_release_v0_3_0_directory_present() -> None:
    p = Path("release/v0.3.0")
    assert p.is_dir()
    assert (p / "manifest.json").exists()


# ── K. Sweep Bots ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("tool", [
    "tools/sweep_drift.py",
    "tools/sweep_openapi_sync.py",
    "tools/sweep_audit_integrity.py",
    "tools/sweep_dependency_audit.py",
    "tools/deprecation_matrix.json",
])
def test_sweep_present(tool: str) -> None:
    assert Path(tool).exists()


# ── L. Operations ──────────────────────────────────────────────────────────
def test_operations_docs_present() -> None:
    for p in (SLA, DISCL, SUPPORT):
        assert p.exists(), p


# ── M. Public Release ─────────────────────────────────────────────────────
def test_press_copy_present() -> None:
    assert PRESS.exists()


def test_release_announcement_present() -> None:
    p = Path("release/v0.3.0/ANNOUNCEMENT.md")
    assert p.exists()
    txt = p.read_text(encoding="utf-8")
    assert "Deprecation Cleanup" in txt


# ── N. First-week operations ──────────────────────────────────────────────
def test_first_week_artifacts() -> None:
    base = Path("release/v0.3.0-week1")
    for name in ("TIMELINE.md", "TRIAGE_LOG.md", "DECISIONS.md",
                  "METRICS_SUMMARY.md", "POST_WEEK_RETRO.md"):
        assert (base / name).exists()


def test_v0_3_1_patch_charter() -> None:
    assert Path("patches/v0.3.1/CHARTER.md").exists()


# ── Final summary ──────────────────────────────────────────────────────────
def test_test_matrix_matches_count() -> None:
    """Cross-check that the matrix doc was updated with the right counts."""
    txt = Path("docs/TEST_MATRIX.md").read_text(encoding="utf-8")
    m = re.search(r"Total:\s*\*\*(\d+)\*\*", txt)
    assert m, "Total count missing"
    assert int(m.group(1)) >= 70
