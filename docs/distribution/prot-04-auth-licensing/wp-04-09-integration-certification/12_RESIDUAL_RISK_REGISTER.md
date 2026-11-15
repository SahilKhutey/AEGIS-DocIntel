# PROT-04.09 — Dossier 12: Residual Risk Register

## 1. Scope & Objective

Every software system operating in untrusted client environments carries residual risks. This register identifies, quantifies, and documents mitigating controls for all residual risks associated with the **AEGIS-DocIntel Protected Demo Edition**.

---

## 2. Risk Assessment Framework

Risks are assessed based on:
- **Likelihood**: Rare (1), Unlikely (2), Possible (3), Likely (4), Frequent (5)
- **Impact**: Insignificant (1), Minor (2), Moderate (3), Major (4), Catastrophic (5)
- **Residual Risk Score**: $\text{Likelihood} \times \text{Impact}$

---

## 3. Residual Risk Matrix

| Risk ID | Threat Scenario | Initial Likelihood | Initial Impact | Mitigating Controls Implemented | Residual Likelihood | Residual Impact | Residual Score | Risk Treatment |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| **RSK-01** | Evaluator reverses downloadable desktop binary to extract proprietary AI engine | 5 | 5 | **Private Engine Isolation**: Proprietary engine routines and prompts run exclusively on server; zero engine code in client bundle (`INT-ENGINE-009`). | 1 | 1 | 1 (Very Low) | **Mitigated** |
| **RSK-02** | Evaluator modifies client memory to spoof `role: "admin"` or bypass UI gates | 4 | 4 | **Server-Enforced Entitlements**: Server recalculates permissions authoritatively on every request, completely ignoring client claims (`INT-ENT-003`). | 1 | 1 | 1 (Very Low) | **Mitigated** |
| **RSK-03** | Evaluator attempts to inspect other evaluators' documents via IDOR | 3 | 5 | **Strict Tenant / License Scoping**: Storage queries filter strictly by verified `ctx.license_id`; foreign ID requests return 404 (`INT-ENT-009`). | 1 | 1 | 1 (Very Low) | **Mitigated** |
| **RSK-04** | Distributed automated bots race quota limits concurrently | 4 | 3 | **Atomic In-Memory Reservations**: Thread-safe mutex acquires locks before budget check; races fail cleanly (`INT-QUOTA-003`, `CROSS-010`). | 1 | 2 | 2 (Low) | **Mitigated** |
| **RSK-05** | Refresh token stolen from evaluator browser | 3 | 4 | **Rotating Token Family Invalidation**: Refresh tokens rotate on every use. Replay of old tokens immediately invalidates the entire family (`INT-SESSION-004`). | 1 | 2 | 2 (Low) | **Mitigated** |
| **RSK-06** | Compromise of server-side license signing private key | 1 | 5 | **Emergency Key Compromise Procedure**: Automated rotation and immediate rejection of all licenses signed with compromised key ID (`INT-LIC-012`). | 1 | 2 | 2 (Low) | **Mitigated** |
| **RSK-07** | Network partition between gateway and upstream foundation model | 3 | 2 | **Conservative Quota Rollback**: Failed computational requests rollback quota reservations; generic errors returned without leaking credentials (`INT-QUOTA-004`, `RES-INT-005`). | 2 | 1 | 2 (Low) | **Accepted** |
| **RSK-08** | Client hardware clock skew causing premature challenge expiration | 2 | 1 | **Configurable Clock Skew Tolerance**: Evaluator challenge-response permits bounded clock skew (60s margin). | 1 | 1 | 1 (Very Low) | **Accepted** |

---

## 4. Residual Risk Conclusion

All high and critical security risks have been effectively mitigated down to Low or Very Low residual ratings. No unmitigated release-blocking security risks remain.
