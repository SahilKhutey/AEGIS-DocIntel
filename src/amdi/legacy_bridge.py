"""Backwards-compatibility bridge (deprecation window closing in 0.4.0).

This file is deliberately noisy: each legacy import emits a FutureWarning
so that 0.3.0 users see IDE hints and CI logs group them under a single
classifier. The sweep bot (tools/sweep_drift.py) scans CI artefacts and
files an issue when the same symbol is imported from >= 2 different files.
"""

from __future__ import annotations

import warnings as _w

_RESOLVE_MAP: dict[str, str] = {
    # Engine renames
    "engine_geometry":     "engines.geometry",
    "engine_matrix":       "engines.matrix",
    "engine_graph":        "engines.graph",
    "engine_template":     "engines.template",
    "engine_frequency":    "engines.frequency",
    "engine_bm25":         "engines.bm25",
    "engine_dense":        "engines.dense",
    "engine_hybrid":       "retrieval.hybrid",
    # Ingestion renames
    "pdf_loader":          "ingestion.pdf",
    "docx_loader":         "ingestion.docx",
    "xlsx_loader":         "ingestion.xlsx",
    "pptx_loader":         "ingestion.pptx",
    "image_loader":        "ingestion.image",
    "text_loader":         "ingestion.text",
    "html_loader":         "ingestion.html",
    "audio_loader":        "ingestion.audio",
    "speech_loader":       "ingestion.speech",
    # Retrieval
    "hybrid_retriever":    "retrieval.hybrid",
    # Compliance
    "pii_engine":          "compliance.pii",
    "pii_redactor":        "compliance.pii",
}


def __getattr__(name: str):  # PEP 562
    target = _RESOLVE_MAP.get(name)
    if target is None:
        raise AttributeError(f"module 'amdi.legacy_bridge' has no attribute {name!r}")
    _w.warn(
        f"Importing {name!r} from 'amdi.legacy_bridge' is deprecated "
        f"and will be REMOVED in v0.4.0. Use 'amdi.{target}'.",
        FutureWarning,
        stacklevel=3,
    )
    from importlib import import_module
    return import_module(f"amdi.{target}")


def _resolve(name: str) -> str | None:
    return _RESOLVE_MAP.get(name)
