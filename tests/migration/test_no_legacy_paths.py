"""Fail if any code references legacy import paths."""

from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_FRAGMENTS = (
    "amdi.src",
    "amdi.",
    "from backend",
    "import backend",
    "engine_geometry",
    "engine_frequency",
    "engine_recurrence",
    "engine_matrix",
    "engine_template",
    "engine_semantic",
    "engine_graph",
    "engine_topology",
    "engine_spectral",
    "engine_tensor",
    "engine_info_physics",
    "hybrid_retriever",
    "retrieval_schemas",
    "retrieval_fusion",
    "retrieval_reranker",
    "retrieval_dedup",
    "retrieval_telemetry",
    "pdf_loader",
    "docx_loader",
    "xlsx_loader",
    "pptx_loader",
    "speech_loader",
    "audio_loader",
    "ocr_engine",
    "pii_engine",
    "redaction_engine",
)


@pytest.mark.parametrize("rel", [".py", ".md", ".rst"])
def test_no_legacy_fragments_anywhere(rel: str) -> None:
    """All forbidden import fragments must be gone."""
    hits: list[tuple[Path, str, int]] = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix not in {".py", ".md", ".rst"}:
            continue
        if any(part in {"build", "dist", ".venv", ".migration_backup", "_archive",
                         ".mypy_cache", ".ruff_cache", "__pycache__"}
                for part in p.parts):
            continue
        # Skip the legacy_bridge itself and migration tests/scripts which explicitly document the old names.
        if p.name in {"legacy_bridge.py", "migrate_imports.py", "test_no_legacy_paths.py", "test_legacy_bridge.py", "verify_migration.py", "STRUCTURE.md", "MIGRATION.md", "DocumentEngine.md", "Systems.md", "README.md"}:
            continue

        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for frag in FORBIDDEN_FRAGMENTS:
                if frag in line:
                    hits.append((p, line.strip(), n))
    assert not hits, "Legacy fragments remain in: " + ", ".join(
        f"{p.relative_to(ROOT)}:{n}" for p, _, n in hits[:10]
    )
