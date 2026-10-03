# AEGIS-DocIntel Architectural Lineage & History

This document preserves the architectural provenance, historical iterations, and consolidation narrative of the AEGIS-DocIntel codebase.

---

## 1. Evolution of the Architecture

The codebase underwent three foundational architectural iterations before arriving at the unified, production-oriented `src/` hierarchy:

```
[AMDI-legacy]           Early proof-of-concept exploring multi-modal document extraction
     │
     ▼
[MDIE-legacy]           Multi-Domain Intelligence Engine focusing on feature extraction
     │
     ▼
[amdi-os-legacy]        12-engine system modularization (Topology, Graph, Info-Physics, etc.)
     │
     ▼
[src/ (Unified AMDI)]   Consolidated canonical pipeline, typed schemas, and REST API
```

---

## 2. Iteration Breakdown & Artifact Provenance

### Iteration 1: AMDI-legacy (`_archive/AMDI-legacy`)
- **Focus:** Initial exploratory codebase for Advanced Multi-Modal Document Intelligence.
- **Characteristics:** Monolithic scripts evaluating OCR parsing, rough document clustering, and ad-hoc linear algebra utilities.
- **Superseded By:** Structured ingestion loaders in `src/ingestion/` and matrix engines in `src/engines/matrix/`.

### Iteration 2: MDIE-legacy (`_archive/MDIE-legacy`)
- **Focus:** Multi-Domain Intelligence Engine.
- **Characteristics:** Introduced domain-specific extractors for legal, financial, and scientific documents. Attempted separate heuristics for each domain.
- **Superseded By:** Universal mathematical representations (simplicial complexes, Laplacian spectra, information entropy) in `src/math_concepts/` and `src/engines/` that generalize across document types rather than relying on brittle per-domain heuristic rules.

### Iteration 3: amdi-os-legacy (`_archive/amdi-os-legacy`)
- **Focus:** AMDI-OS 12-engine modularization.
- **Characteristics:** Divided the mathematical analysis into 12 distinct engines (`amdi-os/mios/`):
  1. Topology & Simplicial Complexes
  2. Spectral Graph Theory
  3. Information Physics & Flow
  4. Tensor Decomposition
  5. Bayesian Belief Calibration
  6. Markov Decision Processes
  7. Combinatorial Optimization & Knapsack
  8. Economic Token Dynamics
  9. Spatial Geometry & DAG
  10. Semantic Vector Space
  11. Reinforcement Learning Context Tuning
  12. Meta-Learning Pipeline Orchestration
- **Reconciliation Audit:** An audit of `amdi-os/src/` vs `src/` revealed:
  - 5 core entry files (`main.py`, `services/`, `observability/`, `memory_engine/`, `llm_service/`) existed exclusively in `src/`.
  - The mathematical engine implementations in `amdi-os/src/engines/` and `src/engines/` were byte-identical.
  - The MIOS engine tests were ported to `tests/test_optimization_suite_engines.py` and `tests/test_master_task_backlog.py`, testing `src/engines/` directly.
- **Outcome:** `src/` was designated the sole canonical implementation root, and `tests/conftest.py` enforced guards against legacy namespace leakage.

---

## 3. Connectors Unification (Phase 4)

Prior to Phase 4, the repository maintained two parallel AI agent connector implementations:
1. `src/ael/connectors/`: Asynchronous export layer connectors used by the Agent Export Layer (AEL).
2. `src/connectors/`: Rich, typed connector hierarchy with token budgeting (`AgentTokenBudget`), response parsing (`ResponseParser`), exponential backoff, dry-run simulation, and framework adapters (`AMDIRetrieverAdapter`, `AegisLlamaIndexReader`).

In Phase 4, `src/connectors/` was reconciled and made canonical:
- Unified both sync (`query`, `send_ueo`) and async (`send`, `stream`) execution paths on `BaseConnector`.
- Added support for both structured `ConnectorConfig` objects and flexible kwargs initialization.
- Exported `CONNECTOR_REGISTRY` and convenience helpers.
- Updated `src/ael/exporter.py` and `src/workflows/export_workflow.py` to route through `src.connectors`.
- Quarantined and pruned redundant `src/ael/connectors/` tree.

---

## 4. Documentation Deduplication

The root directory historically held two parallel documentation trees:
- `Aegis/`: Canonical monograph and technical specifications.
- `Aegis Doc/`: Exact byte-level duplicate (12 `.docx` files, 4.47 MB).

In Phase 4, `Aegis Doc/` was deleted, consolidating documentation in `Aegis/` and `docs/`.

---

## 5. Accessing Historical Code

All historical files and commit states from `_archive/` and previous development phases remain permanently preserved in Git history. They can be inspected or extracted using standard Git commands:

```bash
# View archive commits
git log -- _archive/

# Inspect historical files from a previous commit
git checkout <commit-hash> -- _archive/
```
