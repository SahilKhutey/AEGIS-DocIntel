# WP-04.03 Dossier 08: Abuse & Threat Model

**Work Package:** PROT-04.03  
**Title:** Threat Modeling, Adversarial Attack Vectors & Countermeasure Matrix  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  

---

## 1. Threat Model & Adversary Assumptions

The threat model assumes an untrusted recipient running the AEGIS Protected Demo Edition on an adversarial machine:
1. **Adversary Capabilities:** The evaluator has root/administrator privileges on their machine, can inspect running processes, dump local memory, monitor outbound network packets, alter local files, and script HTTP requests.
2. **Adversary Objectives:**
   - Run the demo across multiple workstations simultaneously without purchasing licenses.
   - Brute-force or harvest valid activation codes.
   - Steal another evaluator's license or deactivate another evaluator's devices.
   - Bypass device quotas via race conditions or replay attacks.

---

## 2. Threat Vector & Countermeasure Matrix

| Threat Vector ID | Adversarial Technique | Impact | Countermeasure & Implementation | Verification Test |
| :--- | :--- | :--- | :--- | :--- |
| **THREAT-DEV-01** | **Casual License Sharing (Multi-Machine)** | Unlicensed concurrent instances | Strict server-side atomic device quota (max 1 active device per evaluation license). | `DEV-002` |
| **THREAT-DEV-02** | **Signature Forgery / Key Spoofing** | Attacker impersonates legitimate device | Asymmetric signature proof over ephemeral nonce and challenge ID. Fails closed on signature mismatch. | `DEV-007`, `DEV-029` |
| **THREAT-DEV-03** | **Challenge Replay Attack** | Re-authenticating using captured challenge response | Challenge is atomically marked `consumed=True` upon first activation; subsequent attempts return `HTTP 400`. | `DEV-010` |
| **THREAT-DEV-04** | **Challenge Expiration Bypass** | Delayed consumption of stale challenge | Epoch timestamps verified under server clock. Challenges expire after 300 seconds. | `DEV-009` |
| **THREAT-DEV-05** | **Activation Code Brute-Forcing** | Enumerating valid vouchers | IP rate limiting (10 attempts/IP/hour) + HMAC-SHA256 non-enumerable code index. | `DEV-024`, `SEC-DEMO-019` |
| **THREAT-DEV-06** | **Race Condition on Device Quota** | Multi-threaded simultaneous activations | Mutual exclusion locks (`threading.Lock`) serialize device registration and slot verification. | `DEV-026` |
| **THREAT-DEV-07** | **Cross-Tenant Device Hijacking (IDOR)** | Evaluator A deactivates Evaluator B's device | Scoped authorization: `device.license_id == ctx.license_id` strictly enforced. | `DEV-019` |
| **THREAT-DEV-08** | **Session Re-use After Deactivation** | Stale session access on removed machine | Immediate cascade revocation of all `SessionRecord` and refresh tokens on device deactivation. | `DEV-003` |
| **THREAT-DEV-09** | **Plaintext Code Leakage from DB/Telemetry** | Exposure of vouchers in logs or storage dumps | Keyed HMAC-SHA256 lookup. Raw codes are never persisted or logged in plaintext. | `DEV-025` |
| **THREAT-DEV-10** | **Installation ID Tampering** | Rebinding challenge to another machine | `installation_id` must match between Stage 1 and Stage 2 payloads. | `DEV-012` |
