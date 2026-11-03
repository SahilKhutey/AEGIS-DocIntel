# AEGIS-DocIntel — Module Inventory Report
**Baseline ID**: AEGIS-BASELINE-001  
**Generated Date**: 2026-11-03  

## 1. Executive Summary
The AEGIS-DocIntel platform source code has been inventoried across its architectural layers.
Total active modules cataloged: 19 key architectural modules.
All core modules have corresponding test suites located in `tests/`.

## 2. Layer Distribution
- **Application & API**: `src.main`, `src.api.auth_guard`, `src.api.routers`
- **Core State & Orchestration**: `src.core.master_state`, `src.core.orchestrator`, `src.core.normalized_document`
- **Spatial & Extraction Engines**: `src.engines.geometry`, `src.engines.graph_reading_order`
- **Intelligence & Compilation**: `src.engines.context`, `src.engines.retrieval`, `src.engines.generation`, `src.engines.intelligence`
- **Governance & Operations**: `src.engines.governance`, `src.operations`, `src.repositories`, `src.services`
- **UI Surfaces**: `src.ui.workbench` (FastAPI-served Workbench SPA)
- **Decoupled Primitives**: `aegis-docprep` (standalone package)
- **Isolated Research**: `src.ael`, `src.math_concepts`

## 3. Verification Findings
- All MVP0 through MVP8 modules demonstrate complete implementation and active integration.
- The 16 mathematical research formalisms from Monograph Appendix E are isolated under `src/ael` and `src/math_concepts` and classified as EXPERIMENTAL.
