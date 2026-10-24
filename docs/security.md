# Security Policy & Internal Audit Findings

This document describes the security posture of AEGIS-DocIntel, details the vulnerabilities identified and resolved during Phase 10, and defines our vulnerability reporting procedures.

---

## Reporting a Vulnerability

We take the security of AEGIS-DocIntel seriously. If you identify a security vulnerability, **please report it privately rather than creating a public GitHub issue**.

- **Email**: `security@aegis-docintel.org` (or contact maintainers privately via GitHub Security Advisories)
- **Encryption**: Include your PGP public key if you require encrypted communications.
- **Response Target**: Initial triage acknowledgment within 48 hours.

Please include:
- A clear description of the vulnerability and potential impact.
- Step-by-step reproduction instructions or a minimal proof of concept.
- Affected component(s) (e.g. `aegis-docprep`, API router, workflow worker).

---

## Phase 10 Internal Audit: Key Findings & Resolutions

During Phase 10, a comprehensive code review of authentication, authorization, and input processing identified the following issues:

### 1. Critical: development authentication bypass (gated — not removed)
- **Issue (Phase 10)**: `dev-<tenant>` bearer tokens and the `aegis-dev-key` API key were accepted regardless of environment.
- **Resolution**: they are accepted **only** when `AEGIS_ENVIRONMENT=development`; the default is `production`, where they return 401. The bypass code path still exists by design for local development and tests. There is no `ALLOW_DEV_BYPASS` variable (earlier versions of this page named one in error). Verified by `tests/test_auth_guard.py`.

### 2. Critical: most routes had no authentication at all (found and fixed in Phase 0)
- **Issue**: probing the live app without credentials showed that 45 of 59 operations accepted anonymous requests — the legacy AEL routes, annotations, admin, advanced and webhook routers had never been wired to authentication. An anonymous caller could export another tenant's document (`GET /v1/documents/{id}/export`) and wipe every document for every tenant (`DELETE /v1/document` → 204).
- **Resolution**: `src/api/auth_guard.py` — a deny-by-default ASGI middleware. Every HTTP route returns 401 without valid credentials unless it is on a short explicit public list (`/health`, `/readiness`, `/docs`, `/redoc`, `/openapi.json`, `/metrics`). New routes are protected automatically. `tests/test_auth_guard.py` probes every operation in the app, so a future unprotected route fails CI.
- **Known exposure**: `/metrics` is public and its series are labelled with `tenant_id`; keep it off the public internet.

### 3. Production Authentication Architecture (Hardened in P0)
- **RS256 JWT Authentication**: `src/api/auth.py` validates RS256 JWT signatures using a cryptographically verified RSA public key (`AEGIS_JWT_PUBLIC_KEY` or file path). It enforces strict RS256 algorithm pinning (rejecting HMAC/HS256 algorithm confusion attacks), validates expiration (`exp`), user identity (`sub`), tenant scoping (`tenant_id`), role permissions (`admin`, `editor`, `viewer`), and optionally validates issuer (`iss`) and audience (`aud`).
- **Production API Keys**: Validates incoming API keys via SHA-256 hash lookup in `AEGIS_API_KEYS` using constant-time comparison (`hmac.compare_digest`). Configuration strictly requires 64-character lowercase hex digest keys and rejects raw plaintext keys in configuration. Plaintext keys are never logged in audit trails.
- **Verification**: Machine-tested by `tests/test_production_auth.py` across positive, expired, invalid key, algorithm confusion, missing claims, unsupported roles, and hash-only lookup scenarios.

### 4. Persistence & Document Lifecycle Integrity (Hardened in P1)
- **Tenant-Scoped Raw Byte Storage**: Document binaries stored in SQLite are strictly scoped by `tenant_id`. Foreign tenant reads and cross-tenant rehydration requests return `None` (404-equivalent) without disclosing document presence.
- **SHA-256 Byte Integrity Verification**: During ingestion, a SHA-256 digest is computed and stored alongside the document record. During rehydration or byte access, the digest is recomputed; any byte tampering raises `DocumentRecoveryError` immediately.
- **Fail-Closed Cascading Deletion**: Document deletion commits a durable `deleting` tombstone in SQLite before downstream stores (vector store, semantic cache) are instructed to delete. If any store fails, the document remains in `delete_failed` status in SQLite and deletion returns `False` (retryable), preventing partial deletions from leaking orphan vectors or cached answers.
- **Crash Recovery Reconciliation**: Interrupted `processing` documents are automatically marked `failed` (`STALE_PROCESSING_INTERRUPTED`) and interrupted `deleting` documents are marked `delete_failed` (`STALE_DELETION_INTERRUPTED`) on startup, preventing zombie states.
- **Verification**: Automated tests in `tests/test_persistence_and_audit.py` and `tests/test_document_deletion.py`.

### 5. Transitive Dependency Vulnerability Triage
- **Issue**: Dependency vulnerability scanning detected known CVE advisories in optional legacy packages.
- **Resolution**: Pruned obsolete packages, pinned modern versions in `requirements-core.txt`, and isolated deep learning components into optional `requirements-ml.txt`. Continuous automated scanning (`pip-audit` / GitHub Dependabot) is now active in CI.

### 3. File Ingestion Path Traversal Hardening
- **Issue**: Document upload filenames were not consistently sanitized before temporary filesystem persistence.
- **Resolution**: Enforced strict UUID-based temporary path mapping (`doc_<uuid4>`) preventing directory traversal via crafted `../../` filenames.

---

## Security Architecture & Assumptions

- **Sandbox Boundary**: The processing engines assume untrusted inputs. File parsing is executed with resource limits to prevent memory exhaustion from crafted "decompression bombs".
- **Internal Audit Status**: The findings documented above represent our own internal rigorous code audits. They do not constitute a formal third-party penetration test.
