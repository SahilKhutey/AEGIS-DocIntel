# PROT-FINAL-05: Deployment Architecture & Trust Boundaries Overview

**Status:** APPROVED | **Classification:** PROPRIETARY / EVALUATION INFRASTRUCTURE
**Commit:** `0b08eac20bda09986248f8cdd3afd1f7c812712e` | **Evaluated:** `2026-11-18T04:40:32.754668+00:00`

## Executive Summary
This document establishes the zero-trust deployment architecture for AEGIS-DocIntel, partitioning the platform into four isolated security zones:
1. **Untrusted Evaluator Client Zone:** Downloaded evaluation client running in the evaluator's local environment.
2. **Public Edge & Gateway Zone:** Public-facing reverse proxy and Evaluation Gateway performing TLS termination, authentication, session validation, device binding, rate limiting, and request sanitization.
3. **Private Processing Engine Zone:** Proprietary document normalization, OCR, table extraction, and reasoning engines isolated on private non-routable container networks (`internal: true`) with zero public port mappings.
4. **Data Infrastructure Zone:** Parameterized multi-tenant PostgreSQL database and encrypted scratch storage strictly accessible only to authenticated internal services.

```
EVALUATOR CLIENT
      │
      ▼ (HTTPS / TLS 1.3)
PUBLIC EDGE / CADDY REVERSE PROXY
      │
      ▼ (HTTP / Port 8000)
EVALUATION GATEWAY
  ├─ Authentication & Session Validation
  ├─ License & Device Integrity Verification
  ├─ Entitlement Resolution & Atomic Quotas
  ├─ Client Tenant Header Stripping (DEP-007)
  └─ Response Traceback & IP Sanitization
      │
      ▼ (Internal Bridge / HMAC-SHA256 Token)
PRIVATE PROCESSING ENGINE
  ├─ Document Processing & Parsing Sandbox
  ├─ Ephemeral Scratchpad Isolation (DEP-005)
  ├─ Isolated LLM Provider Adapters (DEP-006)
  └─ Grounded Intelligence Orchestrator
      │
      ▼ (Private Connection / Least-Privilege Role)
POSTGRESQL DATABASE & STORAGE
```
