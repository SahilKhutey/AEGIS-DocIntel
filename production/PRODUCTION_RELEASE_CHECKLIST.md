# AMDI-OS Production Release Checklist (Annotated Status)

> **STATUS AUDIT NOTICE (October 2026):**
> This checklist represents legacy pre-release planning from early prototyping.
> The benchmark datasets, ground truth pairs, penetration tests, compliance certifications, and signature artifacts referenced here were self-authored exploratory templates, not third-party audits or real document evaluations.
> 
> In accordance with **Phase 1 (Truth Audit & Public Credibility Reset)**, all unverified artifacts have been moved to `_unverified_archive/`. Items below have been updated to **Pending real verification (see STATUS.md)**.

**Target Release:** v1.0.0 (Alpha / Development Snapshot)  
**Status:** ⚠️ Development Prototype — Not Validated for Production  
**Governing Document:** [STATUS.md](STATUS.md) | [docs/ROADMAP.md](docs/ROADMAP.md)

---

## Pre-Release Validation

### 1. Benchmark Dataset
- [ ] 1000+ benchmark documents (synthetic mock dataset quarantined)
- [ ] Document diversity across real-world PDFs (PubLayNet, DocBank, FUNSD)
- [ ] Multi-format coverage tested on real documents

**Owner:** Data Engineering  
**Status:** ⚠️ **Pending real verification (see STATUS.md)** *(Legacy mock dataset moved to `_unverified_archive/benchmark-dataset-mock`)*  
**Roadmap Phase:** Phase 8  

---

### 2. Ground Truth Dataset
- [ ] Master ground truth dataset with human-verified Q&A pairs
- [ ] Real citation accuracy and page grounding annotations
- [ ] Cohen's κ agreement evaluated across independent annotators

**Owner:** ML Engineering  
**Status:** ⚠️ **Pending real verification (see STATUS.md)** *(Synthetic mock predictions quarantined)*  
**Roadmap Phase:** Phase 8  

---

### 3. Performance Report
- [ ] Accuracy benchmarked on public verified corpora
- [ ] Token reduction empirically measured against raw-text baselines
- [ ] Submodular knapsack $(1 - 1/e)$ approximation bound verified on real text collections
- [ ] Real p95 latency envelopes profiled under concurrent load

**Owner:** ML Engineering + QA  
**Status:** ⚠️ **Pending real verification (see STATUS.md)** *(Synthetic 94.2% report moved to `_unverified_archive/performance-report`)*  
**Roadmap Phase:** Phase 9  

---

### 4. Security Audit & Compliance
- [ ] Automated static analysis (`bandit`) in CI
- [ ] Dependency CVE scanner (`pip-audit`) in CI
- [ ] Formal independent penetration test by accredited security firm
- [ ] Accredited SOC 2 Type II / ISO 27001 third-party assessment

**Owner:** Security Team  
**Status:** ⚠️ **Pending real verification (see STATUS.md)** *(Fictional pentest report and compliance JSON moved to `_unverified_archive/security-audit`)*  
**Roadmap Phase:** Phases 10 & 11  

---

### 5. Documentation
- [x] **README.md** — Honest overview, accurate badges, and quickstart (Verified)
- [x] **STATUS.md** — Full credibility audit disclosure (Verified)
- [x] **ROADMAP.md** — 16-phase development roadmap (Verified)
- [x] **Architecture.md** — High-level systems architecture
- [x] **Mathematics.md** — Mathematical formulations

**Owner:** Documentation Team  
**Status:** ✅ Complete (Phase 1 Truth Reset applied)

---

### 6. CI/CD Working
- [x] **.github/workflows/ci.yml** — Matrix build, Ruff linting, Bandit scanning, Pip-audit
- [ ] Multi-OS automated validation across Ubuntu, Windows, and macOS
- [ ] Live coverage reporting and regression lock-in

**Owner:** DevOps  
**Status:** ⚠️ **In Progress (Phase 3)**

---

### 7. Monitoring & Observability
- [ ] Prometheus metrics exported from all core engines
- [ ] Grafana dashboards validated against running ingestion pipelines
- [ ] OpenTelemetry distributed tracing enabled

**Owner:** SRE  
**Status:** ⚠️ **Pending real verification (see STATUS.md)** *(Hooks exist in code; active deployment tracked in Phase 12)*

---

### 8. AI Connectors Validated
- [x] OpenAI, Anthropic, Gemini, DeepSeek, Qwen client code implemented
- [x] LangChain and LlamaIndex adapter classes implemented
- [ ] Load testing and live timeout/rate-limit verification under production traffic

**Owner:** Integration Team  
**Status:** ⚠️ Partially verified (Code implemented and tested with mock responses; live load-testing tracked in Phase 13)

---

### 9. Versioned Release & Cryptographic Signatures
- [ ] Semantic Versioning release tag (`v0.1.0-alpha.1`)
- [ ] Cryptographic release signing via GitHub Actions OIDC / Cosign
- [ ] Verified PyPI package distribution

**Owner:** Release Manager  
**Status:** ⚠️ **Pending real verification (see STATUS.md)** *(Placeholder `.sig` and `.crt` files moved to `_unverified_archive/release-signatures`)*  
**Roadmap Phase:** Phase 13 & 14

---

## Release Decision

**Status:** ⚠️ **NOT APPROVED FOR PRODUCTION — ALPHA / RESEARCH PROTOTYPE ONLY**

All claims must be backed by reproducible test scripts and real-world evaluation per the [16-Phase Roadmap](docs/ROADMAP.md).
