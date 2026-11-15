# PROT-04.09 — Dossier 10: Security Acceptance Criteria Verification

## 1. Acceptance Criteria Framework

To achieve formal release certification for the **Protected Demo Edition**, the platform must satisfy the rigorous acceptance criteria established in **PROT-04 WP-04.09**.

Every criterion has been verified through automated integration tests and empirical audit artifacts.

---

## 2. Acceptance Criteria Scorecard

| Category | Criterion ID | Requirement | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Authentication** | `AC-AUTH-01` | Evaluator identity established via signed PoP challenge | `INT-AUTH-001`, `INT-AUTH-005` | **MET** |
| | `AC-AUTH-02` | Single-device binding per evaluation license | `INT-AUTH-006`, `JOURNEY-C` | **MET** |
| | `AC-AUTH-03` | Anti-replay challenge protection | `INT-AUTH-004` | **MET** |
| | `AC-AUTH-04` | Zero development tokens in production artifacts | `npm run verify:auth` | **MET** |
| **Licensing** | `AC-LIC-01` | Ed25519 digital signature validation | `INT-LIC-001`, `INT-LIC-003` | **MET** |
| | `AC-LIC-02` | Tamper-detection on payload claims | `INT-LIC-002`, `JOURNEY-E` | **MET** |
| | `AC-LIC-03` | Key rotation without circulating license invalidation | `INT-LIC-009`, `INT-LIC-010` | **MET** |
| | `AC-LIC-04` | Emergency key compromise invalidates affected licenses | `INT-LIC-012` | **MET** |
| **Entitlements** | `AC-ENT-01` | Server-side capability enforcement (ignoring client claims) | `INT-ENT-001`, `INT-ENT-002` | **MET** |
| | `AC-ENT-02` | Evaluator privilege escalation strictly denied | `INT-ENT-003`, `CROSS-003` | **MET** |
| | `AC-ENT-03` | IDOR isolation across tenant boundaries | `INT-ENT-009`, `CROSS-001` | **MET** |
| | `AC-ENT-04` | Dynamic administrative overrides take effect instantly | `INT-ENT-007`, `INT-ENT-008` | **MET** |
| **Quotas** | `AC-QUOTA-01` | Strict limits on uploads, queries, comparisons, storage | `INT-QUOTA-001`, `INT-QUOTA-002` | **MET** |
| | `AC-QUOTA-02` | Atomic two-phase reservation prevents race conditions | `INT-QUOTA-003`, `CROSS-010` | **MET** |
| | `AC-QUOTA-03` | Idempotent retries avoid duplicate balance charges | `INT-QUOTA-005` | **MET** |
| | `AC-QUOTA-04` | Failed operations rollback pending reservations | `INT-QUOTA-004` | **MET** |
| **Sessions** | `AC-SESS-01` | Short-lived access tokens (15m) & rotating refresh tokens | `INT-SESSION-001`, `INT-SESSION-003` | **MET** |
| | `AC-SESS-02` | Refresh token replay revokes entire token family | `INT-SESSION-004`, `CROSS-011` | **MET** |
| | `AC-SESS-03` | Server-side logout invalidates credentials immediately | `INT-SESSION-005`, `INT-SESSION-006` | **MET** |
| | `AC-SESS-04` | Revocation propagation SLA < 50ms | `INT-SESSION-013`, `RES-INT-008` | **MET** |
| **Engine Isolation**| `AC-ENG-01` | Private engine requires gateway-issued HMAC token | `INT-ENGINE-001`, `INT-ENGINE-002` | **MET** |
| | `AC-ENG-02` | Engine requests bound to single-use quota reservation | `INT-ENGINE-005`, `INT-ENGINE-006` | **MET** |
| | `AC-ENG-03` | Zero engine code or provider credentials in distribution | `INT-ENGINE-009`, `INT-ENGINE-010` | **MET** |
| **Resilience & DR** | `AC-RES-01` | Subsystems fail closed upon dependency disconnection | `RES-INT-001`, `RES-INT-003` | **MET** |
| | `AC-RES-02` | Database restore does not resurrect revoked credentials | `RES-INT-010` | **MET** |
| | `AC-RES-03` | Audit ledger hash-chain immutability verified | `verify_chain_integrity()` | **MET** |

---

## 3. Formal Assessment

- **Total Acceptance Criteria**: 27
- **Criteria Met**: **27 (100%)**
- **Criteria Unmet / Waived**: **0 (0%)**
- **Defects Blocking Release**: **0 (Zero)**
- **Conclusion**: All security acceptance criteria are completely satisfied.
