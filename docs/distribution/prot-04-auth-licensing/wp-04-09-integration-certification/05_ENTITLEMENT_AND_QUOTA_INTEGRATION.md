# PROT-04.09 — Dossier 05: Entitlement & Quota Integration

## 1. Scope & Objective

This dossier details the integration and verification of **Server-Enforced Entitlements** (WP-04.05) and **Usage Quotas & Resource Governance** (WP-04.06). It verifies that an evaluator can only invoke permitted features within strict computational budgets.

---

## 2. Integrated Enforcement Architecture

```
+---------------------------------------------------------------------------------------+
|                             INCOMING EVALUATOR REQUEST                                |
|                             e.g., POST /v1/evaluation/compare                         |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|  STEP 1: AUTHORITATIVE ENTITLEMENT CHECK                                              |
|  - Resolve active license entitlements from server repository                         |
|  - Apply dynamic administrative overrides (AddOverrideRequest)                        |
|  - Check feature flag: "documents.compare" in entitlements                            |
|    * If False -> 403 Forbidden ("FEATURE_NOT_ENTITLED")                               |
+-------------------------------------------+-------------------------------------------+
                                            | Entitled
                                            v
+---------------------------------------------------------------------------------------+
|  STEP 2: ATOMIC TWO-PHASE QUOTA RESERVATION                                          |
|  - Acquire in-memory license mutex                                                    |
|  - Prune 24-hour sliding window usage timestamps                                      |
|  - Calculate: (consumed + pending_reservations + requested) <= max_limit              |
|    * If False -> 429 Too Many Requests ("QUOTA_EXCEEDED")                             |
|  - Issue reservation_id and transition state to PENDING                               |
+-------------------------------------------+-------------------------------------------+
                                            | Reserved
                                            v
+---------------------------------------------------------------------------------------+
|  STEP 3: COMPUTATIONAL EXECUTION & SETTLEMENT                                         |
|  - If execution SUCCEEDS:                                                             |
|    * Settle reservation (commit to permanent ledger and counter repository)           |
|  - If execution FAILS (Exception / LLM error):                                        |
|    * Rollback reservation (release quota back to evaluator pool)                      |
|  - If reservation EXPIRES (> 300s without settlement):                                |
|    * Reclaim automatically during maintenance cycle                                   |
+---------------------------------------------------------------------------------------+
```

---

## 3. Evaluation Feature Matrix & Quota Policy

### 3.1 Feature Entitlement Definitions
- **Permitted in Evaluation Tier**:
  - `documents.read`: Document listing and metadata inspection.
  - `documents.upload`: Document upload and parsing (.pdf, .md, .txt, .json).
  - `intelligence.query`: Single-document natural language Q&A.
  - `documents.compare`: Multi-document contradiction detection.
  - `evidence.inspect`: Citation and bounding box inspection.
- **Strictly Prohibited in Evaluation Tier**:
  - `users.manage`: Evaluator creating/inviting users (returns HTTP 403).
  - `platform.admin`: Modifying system configuration (returns HTTP 403).
  - `workspaces.create`: Multi-tenant workspace management (returns HTTP 403).
  - `models.configure`: Changing underlying foundational model weights (returns HTTP 403).

### 3.2 Evaluation Quota Limits
| Dimension | Maximum Allowed | Enforcement Mechanism | Failure Response |
| :--- | :--- | :--- | :--- |
| **Document Ingestion** | 5 documents total | Counter check in `DOCUMENT_STORE` | 429 Too Many Requests |
| **Intelligence Queries** | 20 queries / 24h | 24-hour sliding window timestamp ledger | 429 Too Many Requests |
| **Document Comparisons** | 5 comparisons / 24h | 24-hour sliding window timestamp ledger | 429 Too Many Requests |
| **Max File Size** | 10 MB per file | Content-Length & stream length verification | 400 Bad Request |
| **Storage Capacity** | 100 MB cumulative | Cumulative byte count tracking | 429 Too Many Requests |
| **Concurrent Jobs** | 2 simultaneous jobs | Active reservation concurrency lock | 429 Too Many Requests |

---

## 4. Empirical Test Evidence

Results from [feature_matrix_enforcement.json](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/audit/prot-04-09/integration/entitlement/feature_matrix_enforcement.json) and [atomic_reservation_trace.json](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/audit/prot-04-09/integration/quotas/atomic_reservation_trace.json):

| Test ID | Test Scenario | Expected Result | Observed | Status |
| :--- | :--- | :--- | :--- | :--- |
| **INT-ENT-001** | Evaluator calls `/v1/evaluation/usage` | Permitted (HTTP 200) | HTTP 200 | **PASSED** |
| **INT-ENT-002** | Evaluator calls unentitled feature | Prohibited (HTTP 403) | HTTP 403 | **PASSED** |
| **INT-ENT-003** | Evaluator tampers JWT role to `admin` | Ignored (Server authoritative) | HTTP 403 on admin routes | **PASSED** |
| **INT-ENT-007** | Admin disables `documents.compare` mid-session | Subsequent compare calls blocked | HTTP 403 | **PASSED** |
| **INT-ENT-009** | Evaluator inspects foreign document ID | IDOR protection returns 404 | HTTP 404 | **PASSED** |
| **INT-QUOTA-001** | Operation within 20 queries/day limit | Settles cleanly | Quota count = 1 | **PASSED** |
| **INT-QUOTA-002** | Operation exceeding 20 queries/day limit | Rejected with 429 | HTTP 429 | **PASSED** |
| **INT-QUOTA-003** | 10 concurrent threads race for 2 remaining slots | Exactly 2 succeed, 8 fail | 2 True, 8 False | **PASSED** |
| **INT-QUOTA-004** | Operation fails during computation | Reservation rolled back | Quota count unchanged | **PASSED** |
| **INT-QUOTA-005** | Retried request with identical idempotency key | Zero duplicate charges | Count incremented once | **PASSED** |
| **INT-QUOTA-010** | Oversized file upload (> 10 MB) | Rejected before processing | HTTP 400 | **PASSED** |
