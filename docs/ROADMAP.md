# Public Roadmap

A living document. Each box below has an issue tracker label
(`K-deprecation`, `K-perf`, `K-sdk-1-0`, …).

## v0.3.0 — Deprecation Cleanup + Sweep Bots ✅
- [K-deprecation] Close `backend.src.*` import window ✅
- [K-deprecation] Promote `src.amdi.*` warnings to errors in CI ✅
- [K-sweep] Nightly drift, CVE, audit, OpenAPI-sweep bots ✅
- [K-perf] Convert SSE worker progress to typed events
- [K-sdk] Tag Python SDK `0.3.0`; lock resolver hints
- [K-ui] WCAG 2.2 AA audit for React app

## v0.3.1 — First Patch
- [K-perf] Multilingual PII corpus (#1042) ✅
- [K-bot] Helm chart refuses unset jwtSecret (#1043) ✅
- [K-bot] Python 3.13 import compatibility (#1047) ✅
- [K-perf] pytesseract arg sanitization (#1051) ✅
- [K-sdk] Async example merged (#1044) ✅

## v0.4.0 — `legacy_bridge.py` Removal
- [K-remove] Delete `src/amdi/legacy_bridge.py`
- [K-sweep] Tighten drift regex (resolve #1045)
- [K-policy] Public status page
- [K-bench] Promote `docs/Benchmarks.md` to **measured** column
- [K-sdk] C++ SDK joins `1.0.0` candidate track
- [K-perf] Adaptive batching in the `BudgetAllocator`
- [K-obs] Tempo traces replace dev-only OTel no-op

## v0.5.0 — Federated Retrieval (research milestone)
- [K-research] Multi-tenant, multi-region vector routing
- [K-research] Topology-based partition discovery

## v1.0.0 — Hardened
- [K-stable] Freeze public type surface
- [K-stable] All SDKs reach `1.0.0`
- [K-stable] Helm chart promoted
- [K-policy] Add `docs/SLA.md` (uptime, RPO/RTO)
