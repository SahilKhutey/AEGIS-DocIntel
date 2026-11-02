# AEGIS-DocIntel — Known Limitations & Research Boundaries

**Document Status:** Release Verification Audit  
**Classification:** Alpha / Experimental (MVP Evaluation Baseline)  
**Audit Date:** November 2026

---

## 1. Executive Summary

AEGIS-DocIntel is an MVP integration baseline and document intelligence toolkit; **it is not production-ready**. While core capabilities (document ingestion, layout analysis, context budget packing, citation-grounded generation, fact extraction, human-in-the-loop governance, and background job orchestration) are fully implemented and verified with automated test suites, the following architectural and operational boundaries apply.

---

## 2. Research-Target Capabilities vs. Production Features

1. **Topological Persistent Homology:**
   - *Status:* Proposed research architecture (Monograph Appendix E).
   - *Current Implementation:* LayerStatus indicates `is_proposed=True`. Core reading order uses deterministic 2D/3D spatial DAG topological sorting.

2. **Distributed Multi-Cluster Orchestration:**
   - *Status:* Deferred to future enterprise releases.
   - *Current Implementation:* Single-deployment durable job worker with atomic SQLite leases, crash recovery, and bounded exponential backoff retries.

3. **Autonomous Legal or Financial Decisions:**
   - *Status:* Explicitly excluded.
   - *Current Implementation:* All cross-document contradictions and extracted terms are routed through the mandatory Human-in-the-Loop Governance subsystem (`src/engines/governance/`). The engine does not make autonomous binding decisions.

---

## 3. Operational & Runtime Boundaries

1. **Semantic Embedding Fallback:**
   - When no external embedding API key is configured or local PyTorch/SentenceTransformers are unavailable, the system utilizes deterministic feature vectors (`mock_fallback`). This maintains complete pipeline continuity but does not represent dense vector semantic similarity.

2. **Single-Node SQLite Concurrency:**
   - In local developer and benchmark modes, SQLite WAL mode is employed. Concurrent multi-tenant tests pass without data leakage, but high-throughput enterprise workloads require managed PostgreSQL deployment.

3. **External Pilot Verification:**
   - External commercial pilots have not been completed. All benchmarks represent reproducible synthetic and golden corpus evaluations executed under laboratory conditions.

---

## 4. Reconciled Discrepancies

- **Benchmark Latency:** The 1.22s mean latency reported in the README encompasses full multi-layer AMDI pipeline parsing on CPU across diverse multi-column PDFs. Raw text extraction runs in under 0.6s.
- **Corpus Counts:** 62 PDFs represents the specialized real-world PDF corpus; the 78-document suite includes multi-format (DOCX, PPTX, XLSX) integration benchmarks.
- **Latency Bounding:** In local development without connection pooling, health probes complete in p50 < 80ms and p95 < 250ms, passing all automated capacity regression bounds.
