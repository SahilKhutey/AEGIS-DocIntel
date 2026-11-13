# PROT-01: Product Capability Mapping & Runtime Execution Boundary

**Document:** 07_PRODUCT_CAPABILITY_MAP.md  
**Audit Objective:** Map every product capability to its physical runtime execution location and reconcile contradictory status statements (`PROT-F05`).  

---

## 1. Feature Execution Boundary Map

| Feature Priority | Capability | Launch Treatment | Local Demo Execution | Cloud Evaluation Gateway | Private Engine Behind Gateway |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P0** | **Document Upload & Ingestion** | Fully Functional | Drag-and-drop UI, format validation | Payload size & type check, quota check | Node chunking, text extraction |
| **P0** | **Document Inspection & Extraction** | Fully Functional | Node tree rendering, text preview | Metadata delivery, tenant filtering | Hierarchical layout extraction |
| **P0** | **Ask AEGIS (Q&A)** | Fully Functional with Evidence | Chat interface, citation highlight | Daily quota check (20/day), token auth | Submodular context packing, LLM routing |
| **P0** | **Citation & Source Inspection** | Fully Functional | Side-by-side quote viewer | Citation coordinate mapping | Ground-truth verification ledger |
| **P0** | **Document Comparison** | Fully Functional | Diff viewer, severity badges | Comparison quota check (5/day) | Contradiction solver, invariant tracking |
| **P1** | **Governance & Fact Verification** | Guided Walkthrough | Step-by-step verification card | Synthetic verification claims | Abstract interpretation engine |
| **P1** | **Mathematical Representations** | Interactive Showcase | Canvas graph visualization | Graph topological metadata | Sheaf Laplacian spectral solver |
| **P1** | **Pipeline Visualization** | Live Execution View | Stage progress indicators | Telemetry stream | Job orchestrator & worker queue |
| **P1** | **Analytics & Telemetry** | Prepopulated Telemetry | Prometheus/Grafana preview | Pre-computed demo metrics | Live time-series telemetry |
| **P2** | **Developer API / Integrations** | Public Docs / SDK Sample | Code snippets, SDK examples | OpenAPI specification preview | Production REST / gRPC endpoints |

---

## 2. In-Depth Analysis of Finding PROT-F05 (Status Reconciliation)

### Finding Statement:
`docs/status.md` referenced an early alpha prototype with in-process mock answers, whereas release notes claimed full production capabilities with 416 automated tests.

### Reconciliation Resolution:
1. **Source of Truth Reconciled:** `launch/FEATURE_MATRIX.md` was established as the canonical launch contract.
2. **Honest Product Positioning:**
   - **P0 Features:** Functional end-to-end against real services. Evaluators can upload real documents (up to 5), ask queries, inspect verifiable citations, and compare documents.
   - **P1 Showcase Features:** Explicitly labeled as guided showcases using pre-computed synthetic topological models and telemetry, preventing false claims of unreleased beta capabilities.
   - **No Dead Ends:** Every button, tab, and card in the UI has an active, tested code path.
