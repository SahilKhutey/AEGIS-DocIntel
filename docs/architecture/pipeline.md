# Canonical Document Intelligence Pipeline Architecture

This document specifies the unified end-to-end processing pipeline for **AEGIS-DocIntel / AMDI-OS**, consolidated around the central `AMDIOrchestrator` entry point.

---

## 1. High-Level Pipeline Architecture

The primary proposition of AEGIS-DocIntel is a **pre-LLM context compiler**: converting unstructured and multi-modal documents into spatially verified, mathematically structured, privacy-aware context before calling an LLM.

```
+-------------------------------------------------------------------------------+
|                             1. INGESTION & PARSING                            |
|  PDFLoader / DOCXLoader / PPTXLoader / XLSXLoader / ImageOCR                  |
|  - Text extraction, bounding boxes, element normalization                     |
|  - PII masking & privacy compliance redaction (preserves layout)             |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+---------------------------------------+---------------------------------------+
|                       2. 2D SPATIAL & READING-ORDER DAG                       |
|  - Reading order reconstruction via directed acyclic graph (topological sort) |
|  - Section hierarchies, multi-column detection, table grid boundary matrix    |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+---------------------------------------+---------------------------------------+
|                    3. 16 MATHEMATICAL FEATURE ENGINES                         |
|  - Geometry (Voronoi tessellation, bounding box scale-invariance)             |
|  - Matrix (table density, singular value decomposition)                       |
|  - Graph (PageRank centrality, community detection)                           |
|  - Topology (Betti numbers, persistent homology across pages)                 |
|  - Semantic (dense embeddings, multi-provider LiteLLM/OpenAI)                 |
|  - Frequency & Recurrence (TF-IDF, term periodicity)                          |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+---------------------------------------+---------------------------------------+
|                    4. STORAGE, INDEXING & SEMANTIC CACHING                    |
|  - SQLite metadata & raw document byte store (tenant-isolated parameterization)|
|  - FAISS vector store & sparse BM25 indexing                                 |
|  - Semantic cache (L0 memory cache for fast sub-millisecond query reuse)     |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+---------------------------------------+---------------------------------------+
|                     5. SUBMODULAR CONTEXT PACKING                             |
|  - Knapsack token budget optimization ((1 - 1/e)/2 approximation ratio)       |
|  - Maximizes coverage and diversity while strictly bounding LLM context window|
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+---------------------------------------+---------------------------------------+
|                     6. GROUNDED REASONING & EVIDENCE                          |
|  - Prompt injection neutralization (delimiters, BiDi overrides, null bytes)   |
|  - Streaming token delivery with exact element-level citations [1], [2]       |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                       7. SERVING: REST API & DASHBOARD                        |
|  - FastAPI endpoints: /v1/ingest, /v1/documents, /v1/query, /v1/jobs          |
|  - Unified Streamlit Dashboard (dashboard/app.py & dashboard/pages/)          |
+-------------------------------------------------------------------------------+
```

---

## 2. Central Orchestrator (`AMDIOrchestrator`)

The canonical programmatic interface for all document operations is `AMDIOrchestrator` in `src.core.orchestrator`.

```python
from src.core.orchestrator import AMDIOrchestrator

# Initialize the full orchestrator
orch = AMDIOrchestrator()

# Ingest and compile a document
stats = await orch.ingest("path/to/document.pdf")
doc_id = stats["doc_id"]

# Query knowledge with grounded evidence
response = await orch.query("What are the quarterly net revenues?", doc_id=doc_id)
print(response["answer"])
print(response["citations"])

# Stream reasoning tokens in real time
async for token in orch.stream_query("Summarize key risks", doc_id=doc_id):
    print(token, end="")

await orch.close()
```

---

## 3. Workflow Consolidation & Deprecation Strategy

Historically, the repository contained two parallel pipeline layers:
1. `src/workflows/`: Standalone scripts (`IngestWorkflow`, `QueryWorkflow`, `ExportWorkflow`, `BatchWorkflow`).
2. `src/core/orchestrator.py`: The production `AMDIOrchestrator` wired into FastAPI and the SQLite persistence layer.

To eliminate ambiguity and streamline maintenance:
- **Canonical Interface:** All API routers, CLI commands, background jobs, and dashboard controllers invoke `AMDIOrchestrator`.
- **Backward-Compatibility Facade:** `src/workflows/` is maintained as a thin compatibility wrapper for existing tests and scripts.
- **UI Consolidation:** All dashboard pages (`ui/src/pages/`) are unified into `dashboard/pages/`, providing a coherent multi-page Streamlit application in `dashboard/app.py`.
- **Reference Monographs:** Monograph documents have been consolidated from root into `docs/reference/`.

---

## 4. Architectural Invariants

| Dimension | Guarantee | Verification Target |
| :--- | :--- | :--- |
| **Coordinate Invariance** | Normalized coordinates are invariant under uniform rescaling ($W_p, H_p$). | `tests/test_master_state_theorems.py` |
| **Token Budget Bounds** | Context packing never exceeds `max_context_tokens`. | `tests/test_submodular_packer.py` |
| **Tenant Isolation** | SQLite queries bound authenticated `tenant_id` at the SQL driver level. Cross-tenant access yields 404 Not Found. | `tests/test_multitenancy_isolation.py` |
| **Data Sovereignty** | When `AEGIS_ALLOW_EXTERNAL_LLM=false`, remote model calls fail closed and route to certified local fallbacks. | `tests/test_data_governance.py` |
| **Cold-Start Reproducibility** | Fresh virtual environments run tests cleanly using `requirements-core.txt` + `requirements-dev.txt`. | CI `test` job & `scripts/cold_start_check.sh` |
