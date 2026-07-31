# Final Acceptance Checklist — v0.3.0 (Sprint 1–5)

> Every line below is **machine-verifiable** by `scripts/verify_everything.py`
> and **human-verifiable** by following this document.

## A. Code & Repo (Deliverables A, E)

- [ ] `pyproject.toml` exists, version pin present (`re.search(r'version\s*=\s*"\d+\.\d+', …)`).
- [ ] No `from backend.src…` imports remain (`tests/migration/test_no_legacy_paths.py`).
- [ ] `tests/migration/test_canonical_layout.py` is green.
- [ ] `tests/migration/test_legacy_bridge_warning.py` is green.
- [ ] `tests/migration/test_legacy_bridge_removal_readiness.py` shows `xfail` only.

## B. Async Ingestion (Deliverable B)

- [ ] `src/amdi/jobs/worker.py` exists.
- [ ] `POST /v1/documents/upload` returns 202 + `job_id`.
- [ ] `GET  /v1/jobs/{id}/events` emits SSE.
- [ ] `tests/jobs/test_api_upload_async.py` is green.
- [ ] `tests/jobs/test_api_jobs_streaming.py` is green.

## C. Hybrid Retrieval (Deliverable C)

- [ ] 7 methods exist under `src/amdi/retrieval/methods/`.
- [ ] RRF / weighted / calibrated fusion modes.
- [ ] Cross-encoder reranker wired.
- [ ] `tests/retrieval/test_*` (15 files) green.

## D. Benchmarks (Deliverable D)

- [ ] `benchmarks/runners/run_all.py` produces `benchmarks/results/latest.json`.
- [ ] `benchmarks/runners/publish_report.py` writes `benchmarks/docs/Benchmarks.md`.
- [ ] `benchmarks/runners/run_regression.py` exits 0.

## E. Migration & Canonical Layout (Deliverable E)

- [ ] `scripts/verify_migration.py` exits 0.
- [ ] `scripts/detect_orphans.py` produces no findings (or justified review).

## F. Multi-Language SDK (Deliverable F)

- [ ] `proto/amdi.proto` parses; compiled stubs can be regenerated.
- [ ] `sdks/python/src/amdi_sdk/client.py` imports.
- [ ] `sdks/typescript/src/index.ts` builds (`tsc --noEmit`).
- [ ] `sdks/java/pom.xml` exists.
- [ ] `sdks/cpp/CMakeLists.txt` exists.

## G. Security & Reliability (Deliverable G)

- [ ] JWT issue + verify round-trip (`tests/security/test_auth_jwt.py`).
- [ ] Rate limiter denies over-limit (`tests/security/test_rate_limit.py`).
- [ ] Audit chain detects tamper (`tests/security/test_audit_chain.py`).
- [ ] RBAC matrix smoke (`tests/security/test_rbac_matrix.py`).
- [ ] AES-GCM round-trip + rotation (`tests/security/test_crypto_rotation.py`).

## F5. LLMTokenOptimizedExporter (Deliverable F5)

- [ ] Hard-cap property test (`tests/export/test_budget_hard_cap.py`).
- [ ] Markdown / JSON / JSONL exporters (`tests/export/test_*_exporter.py`).

## H. UI (Deliverable H)

- [ ] `ui/streamlit/app.py` parses; 13 pages exist.
- [ ] `ui/react/src/App.tsx` declares 13 routes.
- [ ] `tests/ui/test_*` is green.
- [ ] Capability matrix matches (`tests/ui/test_capability_matrix.py`).

## I. Demo Reel (Deliverable I)

- [ ] `scripts/demo_reel.py` runs end-to-end against a local backend.
- [ ] `tests/demo/test_records_*` is green.
- [ ] Golden trace regenerated (`tests/demo/golden/reel.expected.json`).

## J. Release Discipline (Deliverable J)

- [ ] CHANGELOG.md contains `[0.2.0]` and `[0.3.0]` entries.
- [ ] `release/v0.3.0/MANIFEST.json` exists.
- [ ] `scripts/release_preflight.py` exits 0.

## K. Deprecation & Sweep Bots (Deliverable K)

- [ ] `tools/sweep_drift.py` exits 0 against the current source.
- [ ] `tools/sweep_openapi_sync.py` exits 0.
- [ ] `tools/deprecation_matrix.json` reviewed.

## L. Operations (Deliverable L)

- [ ] `docs/SLA.md`, `docs/DISCLOSURES.md`, `docs/SUPPORT.md` present.
- [ ] `ops/release/tag-v0.3.0.sh` is executable.

## M. Public Release (Deliverable M)

- [ ] Tag `v0.3.0` exists and is signed.
- [ ] GitHub release notes use `release/v0.3.0/ANNOUNCEMENT.md` verbatim.
- [ ] Press copy at `site/press/2026-09-30-v0.3.0.md`.

## N. First Week Operations (Deliverable N)

- [ ] `release/v0.3.0-week1/{TIMELINE,TRIAGE_LOG,DECISIONS,METRICS_SUMMARY,POST_WEEK_RETRO}.md` all present.
- [ ] `scripts/release_patch.py --version 0.3.1` dry-run produces DIFF_STAT.

---

## ✅ Final acceptance

Run in order:

```bash
python scripts/verify_everything.py
```

Expected: `OK · 47/47 invariants passed`. Any `FAIL` points to the
specific cell of `docs/TEST_MATRIX.md` that needs attention.
