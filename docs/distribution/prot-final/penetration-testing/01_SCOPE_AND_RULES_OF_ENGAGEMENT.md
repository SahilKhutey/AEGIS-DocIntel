# Scope and Rules of Engagement

**Assessment Phase:** PROT-FINAL-03  
**Target System:** AEGIS-DocIntel Protected Evaluation Distribution  
**Date:** 2026-11-18T03:21:33.417253+00:00  

---

## 1. In-Scope Components
- **Downloadable Evaluation Package:** `distribution/demo-edition/` (launcher scripts, compose configurations, nginx reverse proxy, demo datasets, package manifests).
- **Client Frontend Source:** `web/src/` (client-side state management, authentication guards, API proxies).
- **Evaluation Gateway Tier:** `services/evaluation_gateway/` (activation service, licensing engine, quota manager, session revocation, error handlers).
- **Core Security Modules:** `src/api/auth.py`, `src/api/auth_guard.py`, `src/security/license_signing.py`, `src/security/device_crypto.py`.

## 2. Out-of-Scope Components
- Production infrastructure hosting live customer data.
- Third-party model provider infrastructure (OpenAI, Anthropic, Google Cloud).
- Physical infrastructure and non-software attacks.

## 3. Rules of Engagement
- All adversarial tests must run against dedicated staging instances.
- Evaluators are assigned synthetic identities (`user-eval-a`, `user-eval-b`).
- Cryptographic keys used during testing are ephemeral test pairs generated in isolated test fixtures.
