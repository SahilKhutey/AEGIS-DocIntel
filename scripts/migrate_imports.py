"""Rewrite import statements to point at the canonical layout.

Handles three families of legacy imports:

    from amdi.foo import Bar   -> from amdi.foo import Bar
    from amdi.foo import Bar           -> from amdi.foo import Bar
    from amdi.foo_old import Bar           -> from amdi.foo import Bar

Plus dotted-package aliases (see `--renames`).

Idempotent — re-running on already-migrated files is a no-op.

    python scripts/migrate_imports.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# (regex pattern on the import string) → (replacement)
RULES: list[tuple[re.Pattern[str], str]] = [
    # amdi.*  → amdi.*
    (re.compile(r"\bbackend\.src\.amdi\b"), "amdi"),
    (re.compile(r"\bbackend\.src\."),       "amdi."),
    (re.compile(r"\bbackend\."),            "amdi."),

    # amdi.* → amdi.*
    (re.compile(r"\bsrc\.amdi\b"), "amdi"),
    (re.compile(r"\bsrc\.main\b"), "amdi.api.app"),


    # Engines + retrieval + ingestion renames
    (re.compile(r"\bamdi\.engines\.engine_geometry\b"),       "amdi.engines.geometry"),
    (re.compile(r"\bamdi\.engines\.engine_frequency\b"),      "amdi.engines.frequency"),
    (re.compile(r"\bamdi\.engines\.engine_recurrence\b"),     "amdi.engines.recurrence"),
    (re.compile(r"\bamdi\.engines\.engine_matrix\b"),         "amdi.engines.matrix"),
    (re.compile(r"\bamdi\.engines\.engine_template\b"),       "amdi.engines.template"),
    (re.compile(r"\bamdi\.engines\.engine_semantic\b"),       "amdi.engines.semantic"),
    (re.compile(r"\bamdi\.engines\.engine_graph\b"),          "amdi.engines.graph"),
    (re.compile(r"\bamdi\.engines\.engine_topology\b"),       "amdi.engines.topology"),
    (re.compile(r"\bamdi\.engines\.engine_spectral\b"),       "amdi.engines.spectral"),
    (re.compile(r"\bamdi\.engines\.engine_tensor\b"),         "amdi.engines.tensor"),
    (re.compile(r"\bamdi\.engines\.engine_info_physics\b"),   "amdi.engines.info_physics"),

    (re.compile(r"\bamdi\.retrieval\.hybrid_retriever\b"),    "amdi.retrieval.hybrid"),
    (re.compile(r"\bamdi\.retrieval\.retrieval_schemas\b"),   "amdi.retrieval.schemas"),
    (re.compile(r"\bamdi\.retrieval\.retrieval_fusion\b"),    "amdi.retrieval.fusion"),
    (re.compile(r"\bamdi\.retrieval\.retrieval_reranker\b"),  "amdi.retrieval.reranker"),
    (re.compile(r"\bamdi\.retrieval\.retrieval_dedup\b"),     "amdi.retrieval.deduplication"),
    (re.compile(r"\bamdi\.retrieval\.retrieval_telemetry\b"), "amdi.retrieval.telemetry"),
    (re.compile(r"\bamdi\.retrieval\.index_store\b"),         "amdi.retrieval.index_store"),

    (re.compile(r"\bamdi\.ingestion\.pdf_loader\b"),          "amdi.ingestion.pdf"),
    (re.compile(r"\bamdi\.ingestion\.docx_loader\b"),         "amdi.ingestion.docx"),
    (re.compile(r"\bamdi\.ingestion\.xlsx_loader\b"),         "amdi.ingestion.xlsx"),
    (re.compile(r"\bamdi\.ingestion\.pptx_loader\b"),         "amdi.ingestion.pptx"),
    (re.compile(r"\bamdi\.ingestion\.speech_loader\b"),       "amdi.ingestion.audio"),
    (re.compile(r"\bamdi\.ingestion\.audio_loader\b"),        "amdi.ingestion.audio"),
    (re.compile(r"\bamdi\.ingestion\.image_loader\b"),        "amdi.ingestion.image"),
    (re.compile(r"\bamdi\.ingestion\.text_loader\b"),         "amdi.ingestion.text"),
    (re.compile(r"\bamdi\.ingestion\.html_loader\b"),         "amdi.ingestion.html"),
    (re.compile(r"\bamdi\.ingestion\.ocr_engine\b"),          "amdi.ingestion.ocr"),

    (re.compile(r"\bamdi\.compliance\.pii_engine\b"),         "amdi.compliance.pii"),
    (re.compile(r"\bamdi\.compliance\.redaction_engine\b"),   "amdi.compliance.redaction"),
]


def rewrite(text: str) -> tuple[str, int]:
    n = 0
    out = text
    for rx, repl in RULES:
        new = rx.sub(repl, out)
        if new != out:
            n += len(rx.findall(out))
            out = new
    return out, n


def _iter_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py")
            if ".migration_backup" not in p.parts
            and "build/" not in p.parts
            and ".venv" not in p.parts]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", type=Path)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    total = 0
    changed: list[tuple[Path, int]] = []

    for f in _iter_files(root):
        src = f.read_text(encoding="utf-8")
        new, n = rewrite(src)
        if n and new != src:
            if args.apply:
                f.write_text(new, encoding="utf-8")
            changed.append((f, n))
            total += n

    print(json.dumps({
        "files_changed": len(changed),
        "imports_rewritten": total,
        "sample": [str(p.relative_to(root)) for p, _ in changed[:10]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
