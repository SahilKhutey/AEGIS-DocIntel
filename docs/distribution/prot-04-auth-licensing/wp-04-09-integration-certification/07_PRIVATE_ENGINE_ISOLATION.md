# PROT-04.09 — Dossier 07: Private Engine Isolation & Gateway Boundary

## 1. Scope & Objective

The **Private Intelligence Engine** represents the core intellectual property of AEGIS-DocIntel: proprietary document ingestion routines, contradiction detection heuristics, structured parsing algorithms, and foundational model prompt templates.

This dossier documents the server-side architectural boundary that isolates the private engine from downloadable evaluator packages and enforces internal HMAC attestation.

---

## 2. Engine Isolation Architecture

```
+---------------------------------------------------------------------------------------+
|                                PUBLIC EVALUATION CLIENT                               |
|                                                                                       |
|  - NO access to engine files: `src/core/private_engine/`, `src/services/ai/`          |
|  - NO access to LLM provider API keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`          |
|  - All requests dispatched exclusively to `/v1/evaluation/*` endpoints                |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | HTTPS Ingress (Strict Session Auth)
                                            v
+---------------------------------------------------------------------------------------+
|                               SECURE EVALUATION GATEWAY                               |
|                                                                                       |
|  1. Authenticates Evaluator & Device Identity                                         |
|  2. Verifies Feature Entitlement ("documents.compare", "intelligence.query")          |
|  3. Atomically Reserves Quota Slot (Returns unique `reservation_id`)                  |
|  4. Constructs Internal HMAC Authorization Token:                                     |
|     token = Base64(payload) || "." || HMAC-SHA256(Base64(payload), SECRET)           |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | Internal Service Channel
                                            v
+---------------------------------------------------------------------------------------+
|                         PRIVATE ENGINE GUARD (Internal RPC)                           |
|                                                                                       |
|  - Validates HMAC-SHA256 signature using internal service secret                      |
|  - Verifies token TTL (< 60 seconds)                                                  |
|  - Enforces Single-Use Request ID Nonce (Anti-replay)                                 |
|  - Validates `quota_reservation_id` presence and one-time consumption                 |
|  - Checks global `revocation_registry` for license validity                           |
|  - Rejects any evaluator attempting `role: "admin"` actions on internal engine       |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | Authorized Attestation
                                            v
+---------------------------------------------------------------------------------------+
|                            PRIVATE INTELLIGENCE ENGINE                                |
|                                                                                       |
|  - Executes computational parsing & contradiction analysis                            |
|  - Ingests trusted context, calls upstream AI foundation APIs                         |
|  - Returns sanitized result payload (citations, contradiction cards)                  |
|  - Zero leakage of raw internal prompts, model weights, or API keys                   |
+---------------------------------------------------------------------------------------+
```

---

## 3. Implementation Specification: Private Engine Guard

The guard is implemented in [src/security/private_engine_guard.py](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/src/security/private_engine_guard.py) and exported in [src/security/__init__.py](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/src/security/__init__.py).

### Key Invariants Enforced:
1. **Cryptographic HMAC Signature**: The token payload cannot be modified without the internal service secret.
2. **Quota Nonce Binding**: Every computational engine request must reference a verified, unconsumed `quota_reservation_id`. Re-use of a reservation is rejected with HTTP 403.
3. **Replay Rejection**: Each internal token bears a unique `request_id`. Presenting the same token twice is rejected.
4. **Revocation Fail-Closed**: If the target license has been revoked in the gateway, the engine guard denies execution immediately.
5. **No Evaluator Admin Escalation**: If an evaluator attempts to invoke administrative engine maintenance operations, the engine guard rejects with HTTP 403.

---

## 4. Empirical Test Evidence

Results from [private_engine_isolation.json](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/audit/prot-04-09/integration/engine/private_engine_isolation.json):

| Test ID | Test Scenario | Expected Result | Observed | Status |
| :--- | :--- | :--- | :--- | :--- |
| **INT-ENGINE-001** | Gateway-issued HMAC token presented to engine | Accepted (EngineAuthContext) | Accepted | **PASSED** |
| **INT-ENGINE-002** | Direct unauthenticated request to engine | HTTP 401 Unauthorized | HTTP 401 | **PASSED** |
| **INT-ENGINE-003** | Engine request with forged tenant context | HTTP 403 Forbidden | HTTP 403 | **PASSED** |
| **INT-ENGINE-004** | Expired engine service token (> 60s) | HTTP 401 Unauthorized | HTTP 401 | **PASSED** |
| **INT-ENGINE-005** | Reused quota reservation ID | HTTP 403 Forbidden | HTTP 403 | **PASSED** |
| **INT-ENGINE-006** | Engine request missing quota reservation ID | HTTP 403 Forbidden | HTTP 403 | **PASSED** |
| **INT-ENGINE-007** | Engine request with revoked license ID | HTTP 403 Forbidden | HTTP 403 | **PASSED** |
| **INT-ENGINE-008** | Evaluator attempting internal engine admin action | HTTP 403 Forbidden | HTTP 403 | **PASSED** |
| **INT-ENGINE-009** | Client artifact file scan for private engine code | Zero engine files found | Clean | **PASSED** |
| **INT-ENGINE-010** | Client artifact file scan for provider API keys | Zero API keys found | Clean | **PASSED** |
