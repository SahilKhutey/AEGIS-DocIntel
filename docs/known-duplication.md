# Known Class Duplication Inventory

This document tracks lower-risk class name duplications across `src/` following the Phase 4 Architectural Deduplication. 
The 7 critical high-risk duplication targets (`BoundingBox`, `Citation`, `DocumentObject`, `UniversalExportObject`, `MarkdownExporter`, `JSONExporter`, `YAMLExporter`) were consolidated into canonical implementations in Steps 4.2–4.6.

The remaining class name duplications have been verified as non-colliding and are cataloged below.

---

## 1. Legitimate Disjoint Scopes (Distinct Concepts)

These classes share names because the term is standard in its respective subsystem, but they operate in completely distinct scopes and are never imported into the same namespace:

| Class Name | Locations | Rationale & Scope |
|---|---|---|
| `ExportFormat` | `src/ael/ueo.py`<br>`src/models/export_object.py` | AEL export format enum (JSON, Markdown, YAML) vs general export schema specification enum. |
| `DocumentStatus` | `src/api/models.py`<br>`src/models/document_object.py` | FastAPI response status serialization schema vs Pydantic model document lifecycle status enum. |
| `QueryRequest` | `src/api/models.py`<br>`src/api/routes/query.py` | Global API request contract vs local route body definition. |
| `QueryResponse` | `src/api/models.py`<br>`src/api/routes/query.py` | Global API response contract vs local route return specification. |
| `FormatError` | `src/export/exceptions.py`<br>`src/ingestion/exceptions.py` | Export serializer formatting exception vs Ingestion file-type parsing exception. |
| `InsufficientDataError` | `src/engines/spectral/exceptions.py`<br>`src/engines/topology/exceptions.py` | Subsystem-specific mathematical domain exceptions (spectral matrix vs topological persistence). |
| `ChunkingConfig` | `src/config.py`<br>`src/ael/elastic_chunker.py` | Global system ingestion chunking configuration vs AEL token-elastic chunker parameters. |
| `QueryType` | `src/engines/fusion/adaptive_fusion.py`<br>`src/engines/retrieval/query_adaptive_budget.py` | Retrieval intent classifier enum vs budget-allocation strategy selector. |
| `ConfidenceScore` | `src/engines/fusion/confidence.py`<br>`src/verification/confidence_scorer.py` | Multi-engine fusion agreement score vs factual verification confidence metric. |

---

## 2. Layer-Scoped Representation Mirrors (Pydantic Schema vs Engine Dataclass)

These classes represent internal mathematical/graph/semantic abstractions that exist in two forms:
1. Canonical Pydantic schemas in `src/models/` for API serialization, validation, and storage.
2. Lightweight engine-specific dataclasses or state containers in `src/core/document_state.py` and `src/engines/` optimized for high-throughput computation and DAG processing without Pydantic validation overhead.

| Concept | Locations | Architectural Role | Future Consolidation Action |
|---|---|---|---|
| `Entity`, `Keyphrase`, `Topic`, `SentimentScore`, `EntityType` | `src/models/semantic_object.py`<br>`src/engines/semantic/semantic_engine.py`<br>`src/core/document_state.py` | Pydantic data models vs runtime semantic extraction dataclasses. | Low risk: convert engine extractors to instantiate `src/models/semantic_object.py` directly during Phase 5. |
| `GraphNode`, `GraphEdge`, `EdgeType`, `GraphMetrics` | `src/models/graph_object.py`<br>`src/engines/graph.py`<br>`src/core/document_state.py` | Pydantic graph models vs in-memory networkx/graph engine nodes. | Maintain separate or align on `src/models/graph_object.py`. |
| `SemanticLayer`, `MatrixLayer`, `GraphLayer` | `src/ael/ueo.py`<br>`src/core/document_state.py` | Universal Export Object payload layers vs internal multi-layer document state DAG. | Keep distinct: UEO is an agent-facing projection, DocumentState is the full internal pipeline DAG. |
| `HyperEdge` / `Hyperedge` | `src/core/document_state.py`<br>`src/engines/matrix/hypergraph.py`<br>`src/engines/hypergraph/hypergraph_engine.py` | Multi-node relationship containers in matrix engine vs hypergraph engine. | Candidate for unification into `src/engines/hypergraph/` in future refactor. |
| `ElementType` | `src/engines/geometry/element.py`<br>`src/models/geometry_object.py` | Geometric element categorization enum. | Both share exact enum values; can unify during engine cleanup. |
| `TableCell` | `src/models/matrix_object.py`<br>`src/engines/matrix/matrix_engine.py` | Pydantic table schema vs matrix numerical calculation cell. | Compatible definitions. |
| `Simplex`, `SimplicialComplex`, `PersistencePoint` | `src/engines/topology/simplex.py`<br>`src/math_concepts/topology.py` | Production topology engine structures vs reference mathematical concepts. | Pure math reference algorithms kept independent of engine pipeline. |
| `Cluster` | `src/engines/spectral/spectral_clustering.py`<br>`src/engines/topology/clusters.py` | Spectral graph partition cluster vs topological cluster. | Mathematically distinct clustering representations. |
| `OCREngine` | `src/ingestion/ocr_engine.py`<br>`src/normalization/ocr.py` | Primary OCR wrapper vs legacy normalization fallback. | Will be unified when normalization pipeline is streamlined. |
| `VerificationResult` | `src/ael/verification.py`<br>`src/export/verification.py` | Agent export validator result vs export engine token verifier. | Can be aliased in future export engine updates. |
| `EmbeddingService` | `src/engines/embeddings/embedding_service.py`<br>`src/engines/semantic/semantic_engine.py` | Main embedding model provider vs semantic local cache client. | Candidate for singleton container injection. |
| `LLMResponse`, `LLMInterface` | `src/engines/llm/llm_interface.py`<br>`src/llm_service/llm_client.py` | Engine interface abstraction vs service wrapper. | Already bridged via adapter patterns. |
