# MVP 1 — Document-to-Context Pipeline Report

## Run Metadata
- Date: 2026-10-27
- Branch: `feat/mvp1-document-context-pipeline`
- Base Commit: `931b91ae51302b9b4e6880af1faa64b6ef82cded`
- Python Version: 3.12.10
- Operating System: Windows 11 / Ubuntu 24.04 (GitHub Actions runner)

## Pipeline Architecture & Verification
- [x] Ingestion validation: Content-type verification, empty file rejection, size limits.
- [x] Text extraction & normalization: Unicode line endings standardized while preserving paragraph breaks.
- [x] Context chunking: Half-open character offsets, contiguous coverage without gaps, bounded overlap.
- [x] Provenance preservation: Mapping chunks to source document and real page numbers from normalized document representations.
- [x] Adapter interface: Structured document context callable independently of FastAPI or database state.
- [x] Quality benchmark gates: Extraction, context packing, privacy, and retrieval gates verified.
- [x] Tenant isolation: Ingestion and retrieval pathways verify tenant boundaries.

## Benchmark Results
Benchmark suite evaluated via `python evaluation/scripts/run_all.py --fail-under-gates`:
- Reading-order Kendall Tau: 1.0 (threshold: >= 0.80)
- Table-cell F1: 1.0 (threshold: >= 0.90)
- Context budget violations: 0.0 (threshold: == 0.0)
- Context packing min approximation ratio: 0.8571 (threshold: >= 0.50)
- Privacy precision: 1.0 (threshold: >= 0.85)
- Privacy recall: 1.0 (threshold: >= 0.85)
- Privacy secret leakage rate: 0.0 (threshold: == 0.0)
- Retrieval MRR: 1.0 (threshold: >= 0.70)
- Retrieval Recall@5: 0.9231 (threshold: >= 0.75)
- Retrieval abstention accuracy: 1.0 (threshold: >= 0.90)

## Security & Secrets Verification
- Bandit static analysis: 0 high/medium issues identified.
- Dependency vulnerability audit (`pip-audit`): 0 known vulnerabilities.
- Gitleaks secret scan: 0 leaks found across complete git history.

## Decision
- [x] MVP 1 ACCEPTED
- [ ] MVP 1 BLOCKED
