# Test Environment & Staging Configuration

**Assessment Phase:** PROT-FINAL-03  
**Date:** 2026-11-18T03:21:33.417253+00:00  

---

## 1. Environment Segregation
Testing runs in an isolated Python test harness utilizing `FastAPI TestClient`, completely decoupling test execution from external networks and live databases.

| Parameter | Staging Value | Purpose |
|---|---|---|
| JWT Signing Algorithm | RS256 | Ephemeral 2048-bit RSA test keys |
| License Algorithm | Ed25519 (EdDSA) | Ephemeral Ed25519 keypair |
| Isolation Domain | Staging / Localhost | Zero external egress required |
| Tenancy Model | Multi-Tenant Staging | Synthetic tenants `tenant-eval-a`, `tenant-eval-b` |

## 2. Automated Clean State Enforcement
Every test fixture automatically resets:
- Activation Service device registry and session store.
- Revocation Registry state and blacklist caches.
- Quota Manager consumption counters.
- Audit Service in-memory event ledgers.
