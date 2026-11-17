# AEGIS-DocIntel — Known Limitations & Honest Product Truth

In adherence to our core engineering principles, we believe in radical transparency over marketing inflation. The following limitations reflect the actual state of the **Product Launch Edition (v1.2.0)** and should be evaluated prior to enterprise deployment.

---

## 1. Licensing & Commercial Terms

- **Dual-License Architecture:**
  - The core extracted package **`aegis-docprep`** (providing spatial reading order, submodular knapsack context packing, and PII redaction) is licensed under the **Apache License, Version 2.0**. It is fully open-source and free for commercial or personal use.
  - The complete platform **AMDI-OS (AEGIS-DocIntel full platform)** is provided under an **Evaluation and Research License**. It allows non-exclusive, non-transferable installation and testing for internal evaluation, academic research, and evaluation of technical benchmarks. Paid commercial licenses are scheduled for General Availability (GA).
- **No Deceptive Marketing:** Do not market or distribute the full platform repository as pure permissive open-source without noting these dual terms.

---

## 2. External Validation & Pilot Status

- **Zero Completed External Pilots:** While internal test coverage exceeds 1,900 automated test items and empirical benchmarks across 78 multi-format documents achieve a 98.7% success rate, **no third-party enterprise pilot customer trials have concluded**.
- **Self-Reported Benchmarks:** Benchmark reports in `benchmarks/` and `docs/reports/` represent our reproducible in-house datasets and scripts (`scripts/run_benchmark.py`). Independent auditor certification has not been performed.

---

## 3. LLM Egress & Model Fallback

- **Egress Policy Restrictions:** In accordance with fail-closed privacy principles, external network egress to commercial LLM providers (e.g. OpenAI, Anthropic) is **disabled by default** (`AEGIS_ALLOW_EXTERNAL_LLM=false`).
- **Default Mode:** Unless explicitly configured with provider keys and external egress enabled, the platform executes deterministic evidence retrieval and structured mock generation. Responses disclose their generation source in the API metadata (`generation_mode: mock | local | provider`).

---

## 4. Complex Layout & Geometry Boundaries

- **Spatial Ambiguity:** While layout-aware reading order recovery handles multi-column articles and tabular grids accurately, complex text wrapping around non-convex polygons or circular callout boxes remains active research.
- **Rotation Normalization:** Documents with mixed portrait and landscape pages require orientation preprocessing. Native automatic rotation deskewing is in progress.

---

## 5. Security & Deployment Safeguards

- **Prometheus Metrics Exposure:** The `/metrics` endpoint labels series with `tenant_id`. Consequently, Nginx reverse proxy configurations **strictly block public access to `/metrics` (returning HTTP 404)** to prevent cross-tenant enumeration.
- **Standalone Development Bypass:** Development authentication tokens (`dev-*`) are strictly rejected whenever `AEGIS_ENVIRONMENT=production` or `demo`. The public live demo accepts only scoped demo credentials.
- **Cosign Provenance Signing:** Cryptographic container signature verification remains a roadmap item for v1.3.0.
