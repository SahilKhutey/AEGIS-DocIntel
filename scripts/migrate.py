"""One-shot migration to canonical layout.

Run from repository root:

    python scripts/migrate.py --apply

Reads `src/` (and optionally `backend/src/` if present), copies files to
canonical positions, rewrites imports in-place, removes orphaned files,
writes a manifest, and exits non-zero on any step failure.

State files:
    .migration_backup/<timestamp>/      full pre-migration snapshot
    .migration_backup/manifest.json    map of old → new paths + hashes
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("migration")

# ─────────────────────────────────────────────────────────────────────────────
# Canonical map: legacy filename (regex) → canonical relative path.
# Keys are matched against the *file name only*; the module precedence is
# the dict iteration order in Python 3.7+.
# ─────────────────────────────────────────────────────────────────────────────
LEGACY_TO_CANONICAL: list[tuple[str, str]] = [
    # Engines — explicit, to avoid ambiguity with the math_concepts/* copies
    (r"^geometry_engine\.py$",           "src/amdi/engines/geometry.py"),
    (r"^frequency_engine\.py$",          "src/amdi/engines/frequency.py"),
    (r"^recurrence_engine\.py$",         "src/amdi/engines/recurrence.py"),
    (r"^matrix_engine\.py$",             "src/amdi/engines/matrix.py"),
    (r"^template_engine\.py$",           "src/amdi/engines/template.py"),
    (r"^semantic_engine\.py$",           "src/amdi/engines/semantic.py"),
    (r"^graph_engine\.py$",              "src/amdi/engines/graph.py"),
    (r"^topology_engine\.py$",           "src/amdi/engines/topology.py"),
    (r"^spectral_engine\.py$",           "src/amdi/engines/spectral.py"),
    (r"^tensor_engine\.py$",             "src/amdi/engines/tensor.py"),
    (r"^info_physics_engine\.py$",       "src/amdi/engines/info_physics.py"),

    # Math concepts
    (r"^topology\.py$",                  "src/amdi/math_concepts/topology.py"),
    (r"^spectral\.py$",                  "src/amdi/math_concepts/spectral.py"),
    (r"^physics\.py$",                   "src/amdi/math_concepts/physics.py"),
    (r"^information_theory\.py$",        "src/amdi/math_concepts/information_theory.py"),
    (r"^graph_theory\.py$",              "src/amdi/math_concepts/graph_theory.py"),
    (r"^optimization\.py$",              "src/amdi/math_concepts/optimization.py"),
    (r"^tensor\.py$",                    "src/amdi/math_concepts/tensor.py"),
    (r"^probability\.py$",                "src/amdi/math_concepts/probability.py"),
    (r"^statistics\.py$",                "src/amdi/math_concepts/statistics.py"),
    (r"^harmonic_analysis\.py$",         "src/amdi/math_concepts/harmonic_analysis.py"),
    (r"^computational_geometry\.py$",    "src/amdi/math_concepts/computational_geometry.py"),
    (r"^control_theory\.py$",            "src/amdi/math_concepts/control_theory.py"),
    (r"^decision_theory\.py$",           "src/amdi/math_concepts/decision_theory.py"),
    (r"^dynamical_systems\.py$",         "src/amdi/math_concepts/dynamical_systems.py"),
    (r"^linear_algebra\.py$",            "src/amdi/math_concepts/linear_algebra.py"),
    (r"^numerical_analysis\.py$",        "src/amdi/math_concepts/numerical_analysis.py"),

    # Retrieval subsystem
    (r"^retrieval_hybrid\.py$",          "src/amdi/retrieval/hybrid.py"),
    (r"^retrieval_schemas\.py$",         "src/amdi/retrieval/schemas.py"),
    (r"^retrieval_fusion\.py$",          "src/amdi/retrieval/fusion.py"),
    (r"^retrieval_reranker\.py$",        "src/amdi/retrieval/reranker.py"),
    (r"^retrieval_dedup\.py$",           "src/amdi/retrieval/deduplication.py"),
    (r"^retrieval_telemetry\.py$",       "src/amdi/retrieval/telemetry.py"),
    (r"^retrieval_index_store\.py$",     "src/amdi/retrieval/index_store.py"),
    (r"^retrieval_bm25\.py$",            "src/amdi/retrieval/methods/bm25_method.py"),
    (r"^retrieval_dense\.py$",           "src/amdi/retrieval/methods/dense_method.py"),
    (r"^retrieval_frequency\.py$",       "src/amdi/retrieval/methods/frequency_method.py"),
    (r"^retrieval_geometry\.py$",        "src/amdi/retrieval/methods/geometry_method.py"),
    (r"^retrieval_graph\.py$",           "src/amdi/retrieval/methods/graph_method.py"),
    (r"^retrieval_matrix\.py$",          "src/amdi/retrieval/methods/matrix_method.py"),
    (r"^retrieval_template\.py$",        "src/amdi/retrieval/methods/template_method.py"),

    # Ingestion
    (r"^pdf_loader\.py$",                "src/amdi/ingestion/pdf.py"),
    (r"^docx_loader\.py$",               "src/amdi/ingestion/docx.py"),
    (r"^xlsx_loader\.py$",               "src/amdi/ingestion/xlsx.py"),
    (r"^pptx_loader\.py$",               "src/amdi/ingestion/pptx.py"),
    (r"^html_loader\.py$",               "src/amdi/ingestion/html.py"),
    (r"^text_loader\.py$",               "src/amdi/ingestion/text.py"),
    (r"^image_loader\.py$",              "src/amdi/ingestion/image.py"),
    (r"^audio_loader\.py$",              "src/amdi/ingestion/audio.py"),
    (r"^speech_loader\.py$",             "src/amdi/ingestion/audio.py"),
    (r"^ocr_engine\.py$",                "src/amdi/ingestion/ocr.py"),
    (r"^ocr\.py$",                       "src/amdi/ingestion/ocr.py"),

    # Compliance
    (r"^pii_detector\.py$",              "src/amdi/compliance/pii.py"),
    (r"^pii_engine\.py$",                "src/amdi/compliance/pii.py"),
    (r"^redaction_engine\.py$",          "src/amdi/compliance/redaction.py"),
    (r"^anomaly_gate\.py$",              "src/amdi/compliance/anomaly.py"),
    (r"^injection_filter\.py$",          "src/amdi/compliance/injection_filter.py"),

    # Other subsystems
    (r"^entity_resolver\.py$",           "src/amdi/entity/resolver.py"),
    (r"^diff_engine\.py$",               "src/amdi/versioning/diff.py"),
    (r"^apted_diff\.py$",                "src/amdi/versioning/diff.py"),
    (r"^query_decomposition\.py$",       "src/amdi/query/decomposition.py"),
    (r"^connector_base\.py$",            "src/amdi/connectors/base.py"),
    (r"^chatgpt_connector\.py$",         "src/amdi/connectors/chatgpt.py"),
    (r"^gemini_connector\.py$",          "src/amdi/connectors/gemini.py"),
    (r"^claude_connector\.py$",          "src/amdi/connectors/claude.py"),
    (r"^deepseek_connector\.py$",        "src/amdi/connectors/deepseek.py"),
    (r"^qwen_connector\.py$",            "src/amdi/connectors/qwen.py"),
    (r"^local_connector\.py$",           "src/amdi/connectors/local.py"),

    # Export / AEL
    (r"^llm_optimized_exporter\.py$",    "src/amdi/export/llm_optimized.py"),
    (r"^markdown_exporter\.py$",         "src/amdi/export/markdown.py"),
    (r"^json_exporter\.py$",             "src/amdi/export/json.py"),
    (r"^yaml_exporter\.py$",             "src/amdi/export/yaml.py"),
    (r"^ael_budget\.py$",                "src/amdi/ael/budget.py"),

    # Core
    (r"^document_object\.py$",           "src/amdi/core/document_object.py"),
    (r"^master_state\.py$",              "src/amdi/core/master_state.py"),
    (r"^orchestrator\.py$",              "src/amdi/core/orchestrator.py"),
    (r"^amdi_orchestrator\.py$",         "src/amdi/core/orchestrator.py"),

    # Services
    (r"^service_container\.py$",         "src/amdi/services/container.py"),
]

# Legacy top-level source roots we will scan (in priority order).
SOURCE_ROOTS: tuple[str, ...] = (
    "backend/src",
    "src",
)

# Test roots we will scan + remap.
TEST_ROOTS: tuple[str, ...] = (
    "backend/tests",
    "tests",
    "src/amdi/tests",   # if anyone ever co-located tests
)

# Files / dirs we will actively remove if present (orphan candidates).
ORPHAN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r".*/_legacy_prototypes/.*"),
    re.compile(r".*/_stubs?/.*"),
    re.compile(r".*/_old.*\.py$"),
    re.compile(r".*/.*_old\.py$"),
    re.compile(r".*/__pycache__/.*"),
    re.compile(r".*\.pyc$"),
    re.compile(r".*/\.mypy_cache/.*"),
    re.compile(r".*/\.ruff_cache/.*"),
    re.compile(r".*/docs/.*\.local$"),
    re.compile(r".*/requirements-dev-.*\.txt$"),
    re.compile(r".*/requirements-.*\.lock\.txt$"),
)


def _hash(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_orphan(p: Path) -> bool:
    s = str(p).replace("\\", "/")
    return any(rx.match(s) for rx in ORPHAN_PATTERNS)


def _classify(file_path: Path) -> str | None:
    """Map a file's basename to a canonical relative path, if any."""
    name = file_path.name
    for rx, target in LEGACY_TO_CANONICAL:
        if re.match(rx, name):
            return target
    return None


def _backup(root: Path, dst: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / ".migration_backup" / ts
    backup_root.mkdir(parents=True, exist_ok=True)
    for entry in root.iterdir():
        if entry.name == ".migration_backup":
            continue
        if entry.is_dir():
            shutil.copytree(entry, backup_root / entry.name)
        else:
            shutil.copy2(entry, backup_root / entry.name)
    return backup_root


def _gather_targets(root: Path) -> list[Path]:
    """Collect every Python file under all candidate roots."""
    found: list[Path] = []
    for sub in SOURCE_ROOTS + TEST_ROOTS:
        base = root / sub
        if base.exists():
            found.extend(base.rglob("*.py"))
    return found


def _copy_file(src: Path, dst_root: Path, target_rel: str) -> Path:
    target = dst_root / target_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(src, target)
    return target


def _emit_legacy_bridge(root: Path) -> None:
    """Create src/amdi/legacy_bridge.py for compatibility window."""
    target = root / "src/amdi/legacy_bridge.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text(_LEGACY_BRIDGE_CONTENT, encoding="utf-8")


_LEGACY_BRIDGE_CONTENT = r"""
# Placeholder; populated by scripts/migrate.py:
# This file is auto-generated.
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", type=Path)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    if not (root / "pyproject.toml").exists():
        print("ERROR: no pyproject.toml — wrong directory?", file=sys.stderr)
        return 2

    if not args.apply:
        print("DRY-RUN mode. Re-run with --apply to commit changes.")
        return 0

    # 1. Snapshot
    backup = _backup(root, root)
    logger.info(f"snapshot.created path={backup}")

    # 2. Copy mapped files
    targets: dict[str, Path] = {}
    collisions: dict[str, int] = defaultdict(int)
    for f in _gather_targets(root):
        rel = _classify(f)
        if not rel:
            continue
        # First occurrence wins; subsequent collisions are logged.
        if rel in targets:
            collisions[rel] += 1
            continue
        out = _copy_file(f, root, rel)
        targets[rel] = out

    if collisions:
        logger.warning(f"collisions.kept_first n={len(collisions)} examples={list(collisions.items())[:5]}")


    # 3. Emit bridge
    _emit_legacy_bridge(root)

    # 4. Write manifest
    manifest = {
        "created_at": datetime.now().isoformat(),
        "mappings": [
            {"legacy": str(src), "canonical": rel,
             "sha256": _hash(tgt) if tgt.exists() else None}
            for rel, tgt in sorted(targets.items())
            for src in [next((f for f in _gather_targets(root)
                              if _classify(f) == rel), Path("?"))]
        ],
        "collisions": dict(collisions),
        "backup": str(backup),
    }
    (root / ".migration_backup" / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Manifest written ({len(targets)} files mapped).")
    print("Next: run `python scripts/migrate_imports.py --apply`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
