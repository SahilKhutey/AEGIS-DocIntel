# AEGIS-DocIntel — Lifecycle Classification Report
**Baseline ID**: AEGIS-BASELINE-001  
**Generated Date**: 2026-11-03  

## 1. Classification Strategy
All repository code has been segmented into strict lifecycle partitions:
- **`MVP-CORE`**: Essential processing primitives (Master State $\mathcal{D}$, Bounding Box DAG, Knapsack context packer, Hybrid Retrieval, Grounded Generation, Auth Guard).
- **`MVP-SUPPORT`**: Operations, review governance, SQLite persistence, and Workbench SPA.
- **`ACTIVE`**: Decoupled standalone packages (`aegis-docprep`).
- **`EXPERIMENTAL`**: Speculative theoretical formalisms (`src/ael`, `src/math_concepts`).
- **`DEPRECATED`**: Legacy pre-migration modules (`backend/src`).
- **`ARCHIVED`**: Historical artifacts quarantined in `_unverified_archive/` (2,048 files).

## 2. Governance Rules Carried Forward
1. No experimental module may be promoted to `MVP-CORE` without passing unit tests, integration benchmarks, and security review.
2. The `_unverified_archive/` directory remains strictly read-only and preserved.
3. Decoupled packages (`aegis-docprep`) maintain minimal zero-deep-learning dependencies (`numpy>=1.26.0`).
