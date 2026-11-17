# PROT-04.06: Quota & Usage Accounting Enforcement

**Work Package:** PROT-04.06  
**Target:** Two-Phase Atomic Capacity Reservation, Durable Usage Ledger, High-Concurrency Race Defense & Multi-Tiered Rate Limiting  
**Status:** **PASSED / CERTIFIED & SIGNED OFF**  
**Detailed Dossiers:** [wp-04-06-usage-quotas/](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/docs/distribution/prot-04-auth-licensing/wp-04-06-usage-quotas/)

---

## 1. Architectural Two-Phase Capacity Reservation

In the AEGIS-DocIntel Protected Demo Edition, capacity checks operate strictly on the trusted Evaluation Gateway before expensive private-engine execution begins:

$$\mathbf{Available} = \mathbf{Limit} - \mathbf{Consumed} - \mathbf{Reserved}$$

$$\mathbf{Reservation\ Rule:} \quad \mathbf{Requested} \le \mathbf{Available}$$

Every operation passes through:
1. **Capacity Reservation:** Capacity across all requested dimensions is atomically locked (`status=PENDING`).
2. **Engine Execution:** Document parsing, OCR, or Ask AEGIS LLM inference runs.
3. **Usage Settlement:** Actual measured units are committed to `consumed`, and unconsumed reservation difference is returned to available capacity (`status=COMMITTED`).
4. **Failure Refund:** On pre-execution failure or cancellation, 100% of the reservation is safely released (`status=RELEASED`).

---

## 2. Multi-Dimensional Quota Policy Matrix

Quota limits are defined across 12 distinct dimensions in versioned policies (`evaluation-basic` v1.0, `evaluation-pro` v1.0):

| Dimension | Unit | Period | Basic Limit | Pro Limit | Enforcement Point |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Documents** | `documents` | Lifetime | **20** | **50** | Gateway Upload |
| **Total Storage** | `bytes` | Lifetime | **100 MB** | **500 MB** | Gateway Upload |
| **Ask AEGIS Queries** | `queries` | Lifetime / Daily | **100 (20/day)** | **500 (100/day)** | Ask AEGIS Endpoint |
| **Document Comparisons** | `comparisons`| Lifetime / Daily | **10 (5/day)** | **50 (25/day)** | Compare Endpoint |
| **LLM Inference Tokens** | `tokens` | Lifetime | **50,000** | **250,000** | Provider Adapter |
| **OCR Pages** | `pages` | Lifetime | **50** | **200** | OCR Processing Worker |
| **Concurrent Jobs** | `jobs` | Concurrent | **2** | **5** | Job Dispatcher |
| **API Requests** | `requests` | Daily | **1,000** | **5,000** | Gateway Ingress |
| **Exports** | `exports` | Lifetime | **5** | **25** | Export Service |
| **Max File Upload** | `bytes` | Per-Operation | **10 MB** | **25 MB** | Streaming Upload Guard |

---

## 3. Dual-Concept Accounting Architecture

The subsystem cleanly separates derived decision state from forensic audit truth:
1. **The Usage Ledger (`UsageEventRepository`):** Authoritative, immutable append-only event log recording `CONSUMPTION`, `RELEASE`, and `ADJUSTMENT` events.
2. **Operational Counters (`QuotaCounterRepository`):** Fast operational counters updated using atomic conditional queries:
   ```sql
   UPDATE evaluation_quota_counters 
   SET reserved = reserved + :amt 
   WHERE consumed + reserved + :amt <= limit_value
   ```
3. **Forensic Reconciliation (`QuotaReconciliationService`):** Periodic scans verify that $\text{Counter}_{\text{consumed}} == \sum \text{Ledger Events}$. Stale abandoned reservations are automatically swept and freed after TTL expiration (`RES-011`, `RECON-005`).

---

## 4. Multi-Tiered Rate Limiting & Abuse Defenses

The `RateLimitService` enforces a continuous sliding-window rate limit (60 requests/minute per license):
- When frequency is exceeded, the gateway responds with **`HTTP 429 Too Many Requests`** and a dynamically computed `Retry-After` header.
- Spoofed client headers (`X-Forwarded-For`) cannot bypass license-scoped rate limits (`RATE-005`).
- Multi-dimensional all-or-nothing reservations prevent partial lock leakage under race conditions (`CONC-003`).

---

## 5. Formal Certification & Verification Evidence

- **Dedicated Protocol Suite:** 60/60 tests passed in `tests/security/evaluation/test_quota_enforcement_protocol.py` across 6 functional suites (Enforcement, Reservation, Concurrency, Metering, Rate Limiting, Reconciliation).
- **Full System Regression:** 290/290 tests passed across all security, gateway, and demo suites in 27.23s.
- **Frontend Security Check:** `npm --prefix web run verify:auth` passed with 0 violations.
- **Audit Evidence Artifacts:** Full suite of 14 audit files generated in `audit/prot-04-06/` via `scripts/generate_audit_prot_04_06.py`.
- **Engineering Dossiers:** Complete 14-document technical specification published in `docs/distribution/prot-04-auth-licensing/wp-04-06-usage-quotas/`.
