"""Core domain types: DocumentObject, MasterStateSpace, AMDIOrchestrator."""

from __future__ import annotations

__doc__: str = """
AEGIS-DocIntel / AMDI-OS — Pre-LLM Document Intelligence Operating System.

Converts unstructured documents (PDF, DOCX, XLSX, PPTX, images, speech/audio)
into synchronized mathematical representations before exporting token-optimized
context to downstream AI agents (ChatGPT, Gemini, Claude, DeepSeek, Qwen, local).

Architectural guarantees (see docs/Mathematics.md):
    * Theorem 6.1 — Spatial DAG Acyclicity
    * Theorem 6.2 — Kahn Topological Determinism
    * Theorem 9.1 — 1/2-Knapsack Bound
    * Monotone Submodular (1 - 1/e) Approximation Bound
"""

__all__ = ["DocumentObject", "MasterStateSpace", "AMDIOrchestrator"]


def __getattr__(name: str) -> object:  # pragma: no cover — exercised lazily
    if name == "DocumentObject":
        from amdi.core.document_object import DocumentObject
        return DocumentObject
    if name == "MasterStateSpace":
        from amdi.core.master_state import MasterStateSpace
        return MasterStateSpace
    if name == "AMDIOrchestrator":
        from amdi.core.orchestrator import AMDIOrchestrator
        return AMDIOrchestrator
    raise AttributeError(f"module 'amdi.core' has no attribute {name!r}")

