# Project Status & Launch Readiness Truth

The canonical, evidence-linked technical status of AEGIS-DocIntel lives in:

**[STATUS.md](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/STATUS.md)**

For the verified Product Launch Edition feature availability breakdown, consult:

**[launch/FEATURE_MATRIX.md](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/launch/FEATURE_MATRIX.md)**

---

## Current Release Baseline (Reconciliation as of v1.1.0 / v1.2.0 Launch Edition)

> [!IMPORTANT]
> Earlier Phase 0 documentation summarized the project as an in-memory research prototype without production authentication or persistence. **That summary is obsolete and has been superseded.**

Automated regression test suites (over 1,900 automated test items) continuously verify the following production-grade capabilities:

1. **Authentication & Ingress Security:** Production RS256 JWT validation, hash-only SHA-256 API-key lookup, deny-by-default HTTP route guard, and dedicated demo sandbox isolation (`tests/test_production_auth.py`, `tests/test_auth_guard.py`, `demo/tests/test_demo_isolation.py`).
2. **Persistence & Lifecycle:** SQLite document store preserving metadata and raw byte payloads across service restarts, with automatic crash recovery, atomic status transitions, and cascading erasure (`tests/test_persistence_and_audit.py`, `tests/test_document_deletion.py`).
3. **Retrieval Grounding & Context Packing:** Layout-aware reading order DAG recovery, submodular knapsack context packing with mathematical approximation guarantees ($(1 - 1/e)/2$), and 100% citation verification with explicit abstention on unanswerable queries (`evaluation/scripts/evaluate_packing.py`, `tests/test_retrieval_grounding.py`).
4. **Empirical Benchmarks:** Multi-format benchmark across 78 real-world files (62 PDFs, 14 DOCX monographs, XLSX, PPTX) achieving 98.7% ingestion success with 220 tables accurately extracted (`scripts/run_benchmark.py`).
5. **Observability & Audit:** Cryptographically chained SHA-256 tamper-evident audit logging and Prometheus metrics (`tests/test_observability_metrics.py`).

---

## Remaining Gaps & Transparent Limitations

In keeping with our product truth commitment:
- **External Pilots:** Independent external enterprise pilot verification has not yet been completed.
- **Model Egress Policy:** External LLM network calls are disabled by default (`AEGIS_ALLOW_EXTERNAL_LLM=false`) and require explicit policy activation.
- **Dual Licensing:** Standalone `aegis-docprep` is Apache 2.0 open-source. The full AMDI-OS workbench is offered under evaluation/research licensing.
