# PROT-04.09 — Dossier 09: Performance & Resilience Testing

## 1. Scope & Objective

This dossier presents empirical latency measurements, throughput capacity, and chaos failure-mode recovery tests across the integrated evaluation platform.

Every security control must operate with minimal overhead to preserve evaluator experience while guaranteeing absolute fail-closed defense under duress.

---

## 2. Empirical Latency Benchmarks

Latency micro-benchmarks were executed over 500 iterations per operation under production simulation conditions.

Empirical data extracted from [latency_benchmarks.json](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/audit/prot-04-09/performance/latency_benchmarks.json):

| Security Operation | Samples | p50 (ms) | p95 (ms) | p99 (ms) | SLA Target | SLA Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ed25519 License Verification** | 500 | 0.0412 | 0.0894 | 0.1420 | < 20.0 ms | **WITHIN SLA** |
| **Atomic Quota Reservation & Release** | 500 | 0.0031 | 0.0078 | 0.0152 | < 10.0 ms | **WITHIN SLA** |
| **Private Engine HMAC Attestation** | 500 | 0.0084 | 0.0195 | 0.0381 | < 10.0 ms | **WITHIN SLA** |
| **Session Token Hash Validation** | 500 | 0.0022 | 0.0051 | 0.0098 | < 5.0 ms | **WITHIN SLA** |
| **Revocation Propagation Lag** | 100 | 0.4500 | 1.8200 | 2.8500 | < 50.0 ms | **WITHIN SLA** |

All cryptographic and state operations execute well beneath 1 millisecond at the 99th percentile, adding negligible overhead to interactive user queries.

---

## 3. Resilience & Chaos Failure Modes (RES-INT-001 - 010)

The system was evaluated against 10 critical operational failure scenarios:

| Test ID | Failure Mode Simulated | Injected Condition | Expected System Behavior | Observed Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RES-INT-001** | Database Offline | Database connection dropped | Fail closed; reject operations safely | HTTP 503 / safe error | **PASSED** |
| **RES-INT-002** | License Authority Offline | Key signing service unreachable | Deny license issuance immediately | HTTP 500/503 (no forged licenses) | **PASSED** |
| **RES-INT-003** | Quota Authority Offline | Quota registry unreachable | Metered actions fail closed | Operations denied safely | **PASSED** |
| **RES-INT-004** | Audit Pipeline Lag | Remote SIEM connection refused | Buffer events in local memory ring buffer | 0 dropped events | **PASSED** |
| **RES-INT-005** | Private Engine Failure | Engine socket connection drops | Return safe generic error (zero stack leak) | Safe 502/503 | **PASSED** |
| **RES-INT-006** | Worker Crash During Ingest | Process killed during parsing | Atomic reservation rolled back | 0 duplicate charges | **PASSED** |
| **RES-INT-007** | Gateway Restart During Refresh | Server restart while token in flight | Discard orphaned child, preserve family | 0 split-brain families | **PASSED** |
| **RES-INT-008** | Revocation Cache Stale | Cache update delayed | Enforce bounded TTL eviction (< 50ms) | Revocation recognized | **PASSED** |
| **RES-INT-009** | Duplicate Event Delivery | Idempotency stress test | Event deduplicated via UUID | Idempotent | **PASSED** |
| **RES-INT-010** | Database Snapshot Restore | Restore prior DB snapshot | Re-apply all post-snapshot revocations | No revoked resurrection | **PASSED** |

---

## 4. Key Takeaways

1. **Sub-Millisecond Overhead**: Cryptographic operations (Ed25519, HMAC-SHA256, SHA-256) are optimized and execute in less than 0.15ms.
2. **Fail-Closed by Default**: When any security dependency fails or loses connectivity, the system defaults to denial.
3. **Non-Resurrection Rule**: Restoring database backups from prior states cannot accidentally restore access to revoked credentials.
